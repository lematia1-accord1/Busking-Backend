
from rest_framework import generics, permissions
#from .models import Bus, Merchant  # Import both models here
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView

# Import serializers here to avoid circular imports
from .serializers import UserSerializer, BusSerializer, BookingSerializer, MerchantSerializer, CustomerSerializer

User = get_user_model()

# User views
class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allow signup for both types

    def get_queryset(self):
        from .models import User  # Import User model here
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create Merchant if user_type is 'merchant'
        if user.user_type == 'merchant':
            from .models import Merchant  # Import Merchant model here
            Merchant.objects.create(user=user, bus_company_name=request.data.get('bus_company_name'))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        from .models import User  # Import User model here
        return User.objects.all()

# Bus views
class BusListCreateView(generics.ListCreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can create buses

    def get_queryset(self):
        from .models import Bus  # Import Bus model here
        return Bus.objects.filter(merchant__user=self.request.user)  # Filter buses by merchant

    def perform_create(self, serializer):
        from .models import Merchant
        serializer.save(merchant=Merchant.objects.get(user=self.request.user))  # Assign merchant to the bus

class BusRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Bus  # Import Bus model here
        return Bus.objects.filter(merchant__user=self.request.user)  # Filter buses by merchant

# Booking views
class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Booking  # Import Booking model here
        return Booking.objects.all()

class BookingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Booking  # Import Booking model here
        return Booking.objects.all()

# Merchant views
class MerchantListView(generics.ListAPIView):
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Merchant  # Import Merchant model here
        return Merchant.objects.all()

class MerchantDetailView(generics.RetrieveAPIView):
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Merchant  # Import Merchant model here
        return Merchant.objects.all()

# Customer views
class CustomerListView(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Customer  # Import Customer model here
        return Customer.objects.all()

class CustomerDetailView(generics.RetrieveAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import Customer  # Import Customer model here
        return Customer.objects.all()

# Signin View
class MyTokenObtainPairView(TokenObtainPairView):
    # No changes needed here, it handles both merchant and passenger logins
    pass