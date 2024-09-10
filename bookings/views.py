import logging
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import render, redirect
from .forms import BusForm

from .models import Bus, Merchant, Booking, Customer
from .serializers import UserSerializer, BusSerializer, BookingSerializer, MerchantSerializer, CustomerSerializer

# Set up logging
logger = logging.getLogger(__name__)

# User model
User = get_user_model()

# User views
class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Allow signup for both types

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create Merchant if user_type is 'merchant'
        if user.user_type == 'merchant':
            Merchant.objects.create(user=user, bus_company_name=request.data.get('bus_company_name'))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

# Bus views
class BusListCreateView(generics.ListCreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can create buses

    def get_queryset(self):
        return Bus.objects.filter(merchant__user=self.request.user, merchant__approved=True)  # Filter buses by merchant
    
    def perform_create(self, serializer):
        merchant = get_object_or_404(Merchant, user=self.request.user)
        if merchant.approved:
            serializer.save(merchant=merchant)
        else:
            raise ValidationError("Merchant must be approved to add buses.")
    
    def create_bus(request):
        if request.method == 'POST':
            form = BusForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('bus_list')  # Redirect to a success page or list of buses
        else:
            form = BusForm()
    
        return render(request, 'create_bus.html', {'form': form})

class BusRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bus.objects.filter(merchant__user=self.request.user, merchant__approved=True)  # Filter buses by merchant

# Booking views
class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.all()

class BookingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.all()

# Merchant views
class MerchantListView(generics.ListAPIView):
    serializer_class = MerchantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Merchant.objects.all()

class ApproveMerchantView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        merchant_id = request.data.get('merchant_id')
        merchant_to_approve = get_object_or_404(Merchant, id=merchant_id)

        # Check if the requesting user is the default merchant
        requesting_merchant = get_object_or_404(Merchant, user=request.user)
        if requesting_merchant.is_default:
            merchant_to_approve.approved = True
            merchant_to_approve.save()
            return Response({"detail": "Merchant approved successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Only the default merchant can approve other merchants."}, status=status.HTTP_403_FORBIDDEN)

class MerchantDetailView(generics.RetrieveAPIView):
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
    lookup_field = 'pk'

# Customer views
class CustomerListView(generics.ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.all()

class CustomerDetailView(generics.RetrieveAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.all()

# Function to handle bus seat bookings
def book_bus(request, bus_id, number_of_seats):
    bus = get_object_or_404(Bus, id=bus_id)

    try:
        logger.debug(f"Attempting to book {number_of_seats} seats on bus {bus.name}.")
        bus.book_seats(number_of_seats)
        logger.debug(f"Booking successful for bus {bus.name}. Remaining seats: {bus.available_seats}.")
    except ValidationError as e:
        logger.error(f"Error during booking: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

    buses = Bus.objects.all().values('name', 'total_seats', 'available_seats')
    logger.debug("Returning the list of all buses with their available seats.")
    return JsonResponse(list(buses), safe=False)

# Signin View
class MyTokenObtainPairView(TokenObtainPairView):
    pass
