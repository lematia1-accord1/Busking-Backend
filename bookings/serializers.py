from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Bus, Booking, Merchant, Customer, Payment
from .models import Destination, Route
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with controlled field access.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'user_type']
        extra_kwargs = {
            'user_type': {'write_only': True},
            'password': {'write_only': True},  
        }

    def create(self, validated_data):
        user_type = validated_data.pop('user_type', None)
        
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        if user_type:
            user.user_type = user_type
            user.save()

        return user

    
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
            'bus_routes': {'required': False},  
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
            'transaction_id': {'read_only': True},  
            'currency': {'read_only': True},  
            'is_paid': {'read_only': True},  
            'status': {'read_only': True},  
            'payment_method': {'read_only': True}, 
        }


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for Booking model. Includes nested BusSerializer and a custom payment field.
    """
    bus = serializers.PrimaryKeyRelatedField(queryset=Bus.objects.all())
    payment = serializers.SerializerMethodField() 
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'bus', 'name', 'email', 'phone', 'seats', 'booking_date', 
            'payment_method', 'pickup_location', 'pickup_time', 
            'expected_journey_duration', 'destination', 'is_paid', 'payment', 'amount'
        ]
        extra_kwargs = {
            'pickup_time': {'required': False},  
            'expected_journey_duration': {'required': False},  
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'amount' in representation:
            representation['amount'] = float(representation['amount'])
        if 'bus' in representation and isinstance(representation['bus'], dict):
            representation['bus']['price'] = float(representation['bus'].get('price', 0))
        return representation


class MerchantSerializer(serializers.ModelSerializer):
    """
    Serializer for Merchant model with nested UserSerializer.
    """
    user = UserSerializer() 

    class Meta:
        model = Merchant
        fields = ['id', 'user', 'bus_company_name', 'approved', 'is_default']
        extra_kwargs = {
            'user': {'read_only': True},  
        }

    def create(self, validated_data):
        user_data = validated_data.pop('user')  
        user = User.objects.create(**user_data)  
        merchant = Merchant.objects.create(user=user, **validated_data)  
        return merchant


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model with nested UserSerializer.
    """
    user = UserSerializer() 

    class Meta:
        model = Customer
        fields = ['id', 'user']
        extra_kwargs = {
            'user': {'read_only': True},  
        }


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['id', 'name', 'city', 'state']


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'name', 'start_location', 'end_location']

    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['email'] = user.email  

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = self.user.username
        data['email'] = self.user.email  

        return data
    



