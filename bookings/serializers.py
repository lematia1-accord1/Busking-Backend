from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bus, Booking

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ['id', 'name', 'departure_time', 'arrival_time', 'price']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'bus', 'name', 'email', 'phone', 'seats']
