from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import nearby_filter
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .serializer import UserSerializer, RegisterSerializer
from datetime import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsOwnerOrAdmin, IsUserOrAdmin
from .models import Stadium, Booking, TaskOrder, Users
from .serializer import StadiumSerializer, BookingSerializer

class HelloAPIView(APIView):
    def get(self, request):
        return Response({"message" : "hello"})

class RegisterViewSet(viewsets.GenericViewSet):
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)

class LogoutViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["delete"])
    def logout(self, request):
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)

class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Users.objects.filter(role='User')
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

class StadiumAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Stadium.objects.filter(owner__id=request.user.id)
        serializer = StadiumSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data['owner'] = request.user.id
        serializer = StadiumSerializer(data=request.data, many=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class StadiumDetailAPIView(APIView):
    def get(self, request, pk):
        queryset = get_object_or_404(Stadium, id=pk)
        serializer = StadiumSerializer(queryset, many=False)
        return Response(serializer.data)


class StadiumUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def patch(self, request, pk):
        queryset = get_object_or_404(Stadium, id=pk)
        serializer = StadiumSerializer(
            instance=queryset, data=request.data, many=False, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        queryset = get_object_or_404(Stadium, id=pk)
        queryset.delete()
        return Response({
            'message': 'Stadium deleted successfully!'
        }, status=204)


class StadiumsFilterAPIView(APIView):
    def get(self, request):
        user_latitude = request.query_params.get('user_latitude', 41.316)
        user_longitude = request.query_params.get('user_longitude', 64.420)

        time_from = request.query_params.get('time_from', "2025-06-13 10:00")
        time_to = request.query_params.get('time_to', "2025-06-13 11:00")

        if time_from and time_to:
            time_from = datetime.strptime(time_from, '%Y-%m-%d %H:%M')
            time_to = datetime.strptime(time_to, '%Y-%m-%d %H:%M')
            queryset = Stadium.objects.exclude(
                (Q(booking__start_time__lte=time_to)
                 & Q(booking__end_time__gte=time_from))
            )
        else:
            queryset = Stadium.objects.all()
        return Response(nearby_filter(user_latitude, user_longitude, queryset))


class BookAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin, IsUserOrAdmin]

    def get(self, request):
        queryset = Booking.objects.filter(stadium__owner__id=request.user.id)
        serializer = BookingSerializer(queryset, many=True)
        return Response(serializer.data)


class OwnerDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        queryset = get_object_or_404(Users, id=pk, role='Owner')
        serializer = UserSerializer(queryset, many=False)
        return Response(serializer.data)


class BookCancelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, pk):
        queryset = get_object_or_404(Booking, id=pk)
        if queryset.status == 'Pending':
            queryset.status = 'Canceled'
            queryset.is_busy = False
            queryset.save()
            return Response({
                'message': 'Booking canceled successfully!'
            }, status=200)

        return Response({
            'error': 'Invalid status.'
        }, status=400)



class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        queryset = get_object_or_404(Users, id=pk, role='User')
        serializer = UserSerializer(queryset, many=False)
        return Response(serializer.data)

class BookCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsUserOrAdmin]

    def post(self, request):
        request.data['user'] = request.user.id
        serializer = BookingSerializer(data=request.data, many=False)

        if Booking.objects.filter(
                Q(start_time__lte=datetime.strptime(request.data.get('start_time'), '%Y-%m-%d %H:%M:%S'))
                & Q(end_time__gte=datetime.strptime(request.data.get('end_time'), '%Y-%m-%d %H:%M:%S'))
                & Q(stadium__id=int(request.data['stadium']))
        ).exists():
            return Response({
                'error': 'The stadium is occupied in the current interval.',
            }, status=400)

        if serializer.is_valid():
            serializer.save()

            time_now = datetime.now()
            target = datetime.strptime(request.data.get('end_time'), '%Y-%m-%d %H:%M:%S')

            diff = target - time_now
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=diff.seconds,
                period=IntervalSchedule.SECONDS
            )
            task = PeriodicTask.objects.create(
                interval=schedule,
                name='Time Checker',
                task='app.task.stadium_time_checker',
            )
            TaskOrder.objects.create(
                book=Booking.objects.get(id=serializer.data['id']),
                periodic_task=task,
            )

            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class FilterStadiumsByOwnerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, pk):
        queryset = Stadium.objects.filter(owner__id=pk)
        serializer = StadiumSerializer(queryset, many=True)
        return Response(serializer.data)


class OwnerListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        queryset = Users.objects.filter(role='Owner')
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

