from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bus, Booking, Merchant, Customer, Payment

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with controlled field access.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']
        extra_kwargs = {
            'user_type': {'write_only': True},  # Prevents user_type from being exposed via API
        }

class BusSerializer(serializers.ModelSerializer):
    """
    Serializer for Bus model. Includes a read-only field for available_seats.
    """
    available_seats = serializers.ReadOnlyField()

    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'departure_time', 'arrival_time', 'price', 
            'bus_routes', 'license_plate', 'total_seats', 'available_seats'
        ]
        extra_kwargs = {
            'bus_routes': {'required': False},  # Allows bus_routes to be optional
        }

class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model with certain fields marked as read-only.
    """
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'booking', 'amount', 'transaction_id', 
            'timestamp', 'refunded', 'currency', 'is_paid', 'status', 'payment_method'
        ]
        extra_kwargs = {
            'transaction_id': {'read_only': True},  # Transaction ID should be immutable
            'currency': {'read_only': True},  # Currency should not be modifiable via API
            'is_paid': {'read_only': True},  # Internal field for payment status
            'status': {'read_only': True},  # Managed internally
            'payment_method': {'read_only': True},  # Set during the transaction
        }

class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model. Includes nested BusSerializer and a custom payment field.
    """
    bus = BusSerializer()  # Nested serializer for bus details
    payment = serializers.SerializerMethodField()  # Custom method to retrieve payment info

    class Meta:
        model = Booking
        fields = [
            'id', 'bus', 'name', 'email', 'phone', 'seats', 'booking_date', 
            'payment_method', 'pickup_location', 'pickup_time', 
            'expected_journey_duration', 'destination', 'is_paid', 'payment'
        ]
        extra_kwargs = {
            'pickup_time': {'required': False},  # Optional field
            'expected_journey_duration': {'required': False},  # Optional field
        }

    def get_payment(self, obj):
        """
        Custom method to retrieve the payment details for a booking.
        """
        try:
            payment = Payment.objects.get(booking=obj)
            return PaymentSerializer(payment).data
        except Payment.DoesNotExist:
            return None

class MerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for Merchant model with nested UserSerializer.
    """
    user = UserSerializer()  # Nested serializer for user details

    class Meta:
        model = Merchant
        fields = ['id', 'user', 'bus_company_name', 'approved', 'is_default']
        extra_kwargs = {
            'user': {'read_only': True},  # User details should not be modifiable via API
        }

class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model with nested UserSerializer.
    """
    user = UserSerializer()  # Nested serializer for user details

    class Meta:
        model = Customer
        fields = ['id', 'user']
        extra_kwargs = {
            'user': {'read_only': True},  # User details should not be modifiable via API
        }
