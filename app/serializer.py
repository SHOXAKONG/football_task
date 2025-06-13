from rest_framework import serializers
from app.models import Users, Stadium, Booking


class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(max_length=200, write_only=True)

    class Meta:
        model = Users
        fields = ['first_name', "last_name", "username", "email", "password", "password_confirm", 'role']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Password does not match !")
        if len(data['password']) <= 7:
            raise serializers.ValidationError("Password should be 8 and more than 8!")
        return data



    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Users(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ('id', 'username', 'email')



class StadiumSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = Stadium
        fields = ('id', 'name', 'latitude', 'longitude', 'address', 'contact', 'image', 'price', 'owner')


class BookingSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    class Meta:
        model = Booking
        fields = ('id', 'phone_number', 'start_time', 'end_time', 'is_busy', 'status', 'user', 'stadium')