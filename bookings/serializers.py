from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bus, Booking, Merchant, Customer

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ['id', 'name', 'departure_time', 'arrival_time', 'price', 'destinations', 'bus_routes', 'license_plate', 'total_seats', 'available_seats']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'bus', 'name', 'email', 'phone', 'seats', 'booking_date', 'payment_method', 'pickup_location', 'pickup_time', 'expected_journey_duration', 'destination', 'setoff_time', 'expected_arrival_time']

class MerchantSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested UserSerializer for merchant details

    class Meta:
        model = Merchant
        fields = ['id', 'user', 'bus_company_name']

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Nested UserSerializer for customer details

    class Meta:
        model = Customer
        fields = ['id', 'user']
