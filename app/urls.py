from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('register', views.RegisterViewSet, 'register')
router.register('', views.LogoutViewSet, 'logout')
urlpatterns = [
    path('', include(router.urls)),
    path('user-detail/<int:pk>/', views.UserDetailAPIView.as_view()),
    path('owners/', views.OwnerListAPIView.as_view()),
    path('users/', views.UserListAPIView.as_view()),
    path('stadiums/', views.StadiumAPIView.as_view()),
    path('stadium/<int:pk>/', views.StadiumDetailAPIView.as_view()),
    path('stadiums/filter/owner/<int:pk>/', views.FilterStadiumsByOwnerAPIView.as_view()),
    path('bookings/', views.BookAPIView.as_view()),
    path('booking-cancel/<int:pk>/', views.BookCancelAPIView.as_view()),
    path('stadium-update/<int:pk>/', views.StadiumUpdateAPIView.as_view()),
    path('stadiums/filter/', views.StadiumsFilterAPIView.as_view()),
    path('booking/', views.BookCreateAPIView.as_view()),
    path('owner-detail/<int:pk>/', views.OwnerDetailAPIView.as_view()),

]
