import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
import requests
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from rest_framework.views import APIView
from .easypay_mobile_money import EasyPayMobileMoney
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from .models import Bus, Merchant, Booking, Customer, Payment
from .serializers import UserSerializer, BusSerializer, BookingSerializer, MerchantSerializer, CustomerSerializer
from .forms import BookingForm, BusSearchForm, BusForm

# Set up logging
logger = logging.getLogger(__name__)

# User model
User = get_user_model()

# User Views
class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.user_type == 'merchant':
            Merchant.objects.create(user=user, bus_company_name=request.data.get('bus_company_name'))

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserChangeForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

def bus_details(request, bus_id):
    """View to retrieve details for a specific bus."""
    bus = get_object_or_404(Bus, id=bus_id)
    data = {
        'id': bus.id,
        'name': bus.name,
        'departure_time': bus.departure_time,
        'arrival_time': bus.arrival_time,
        'price': bus.price,
        'total_seats': bus.total_seats,
        'available_seats': bus.available_seats,
        'bus_routes': bus.bus_routes,
    }
    return JsonResponse(data)


# Bus Views
class BusListCreateView(generics.ListCreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bus.objects.filter(merchant__user=self.request.user, merchant__approved=True)

    def perform_create(self, serializer):
        merchant = get_object_or_404(Merchant, user=self.request.user)
        if merchant.approved:
            serializer.save(merchant=merchant)
        else:
            raise ValidationError("Merchant must be approved to add buses.")


class SearchBusesView(generics.ListAPIView):
    serializer_class = BusSerializer

    def get_queryset(self):
        search_query = self.request.query_params.get('search', '')
        if search_query:
            return Bus.objects.filter(name__icontains=search_query)
        return Bus.objects.all()


class BusRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bus.objects.filter(merchant__user=self.request.user, merchant__approved=True)


def view_available_buses(request):
    buses = Bus.objects.filter(merchant__approved=True)
    return render(request, 'bus_list.html', {'buses': buses})


# Booking Views
class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.all()
    
class BookingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


@login_required
def book_ticket(request, bus_id=None):
    bus = get_object_or_404(Bus, id=bus_id) if bus_id else None
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            if bus:
                seats = int(request.POST['seats'])
                if seats <= bus.available_seats:
                    booking = Booking(user=request.user, bus=bus, seats_booked=seats)
                    booking.save()
                    bus.available_seats -= seats
                    bus.save()
                    return redirect('payment_process', booking_id=booking.id)
                else:
                    messages.error(request, "Not enough seats available.")
                    return redirect('book_ticket', bus_id=bus_id)
            return redirect('booking_history')
    else:
        form = BookingForm()
    return render(request, 'book_ticket.html', {'form': form, 'bus': bus})


@login_required
def payment_process(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'payment.html', {'booking': booking})


@login_required
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    send_mail(
        'Booking Confirmation',
        f'Your booking for {booking.bus.name} is confirmed.',
        'from@example.com',
        [booking.user.email],
        fail_silently=False,
    )
    return redirect('booking_history')


@login_required
def booking_history(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'booking_history.html', {'bookings': bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    bus = booking.bus
    bus.available_seats += booking.seats_booked
    bus.save()
    booking.delete()
    return redirect('booking_history')


# Admin Views
@staff_member_required
def manage_buses(request):
    buses = Bus.objects.all()
    return render(request, 'manage_buses.html', {'buses': buses})


@staff_member_required
def booking_stats(request):
    from django.db.models import Count
    stats = Booking.objects.values('bus').annotate(total=Count('id'))
    return render(request, 'booking_stats.html', {'stats': stats})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def browse_buses(request):
    """View to list all buses."""
    buses = Bus.objects.all()
    data = [{
        'id': bus.id,
        'name': bus.name,
        'departure_time': bus.departure_time,
        'arrival_time': bus.arrival_time,
        'price': bus.price,
        'total_seats': bus.total_seats,
        'available_seats': bus.available_seats,
    } for bus in buses]
    return JsonResponse(data, safe=False)


# Merchant Views
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


# Customer Views
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


# Booking and Payment Views
class BookBusView(View):
    def post(self, request, *args, **kwargs):
        bus_id = request.POST.get('bus_id')
        number_of_seats = request.POST.get('number_of_seats')
        bus = get_object_or_404(Bus, id=bus_id)
        
        try:
            logger.debug(f"Attempting to book {number_of_seats} seats on bus {bus.name}.")
            bus.book_seats(number_of_seats)
            logger.debug(f"Booking successful for bus {bus.name}. Remaining seats: {bus.available_seats}.")
        except ValidationError as e:
            logger.error(f"Error during booking: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        
        if bus.is_full:
            messages.error(request, "The bus is fully booked. Please search for another bus.")
            return redirect('search_buses')

        booking = Booking.objects.create(
            bus=bus,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            seats=number_of_seats,
            booking_date=request.POST.get('booking_date'),
            payment_method=request.POST.get('payment_method'),
            pickup_location=request.POST.get('pickup_location'),
            pickup_time=request.POST.get('pickup_time'),
            expected_journey_duration=request.POST.get('expected_journey_duration'),
            destination=request.POST.get('destination'),
        )

        # Initiate EasyPay transaction via requests
        url = 'https://api.easypay.ug/endpoint'  # Replace with the correct EasyPay API URL
        headers = {
            'Authorization': f'Bearer {settings.EASYPAY_ACCESS_TOKEN}',  # Use settings for tokens
            'Content-Type': 'application/json'
        }
        data = {
            'amount': booking.calculate_total_price(),  # Replace with actual method to calculate price
            'currency': 'UGX',  # Or your relevant currency
            'reference': booking.id
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            payment_data = response.json()
            logger.info(f"Payment initiated successfully. Response: {payment_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during payment initiation: {str(e)}")
            return JsonResponse({'error': 'Payment initiation failed. Please try again.'}, status=500)

        return redirect('booking_success', booking_id=booking.id)

class EasyPayCallbackView(View):
    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get('transaction_id')
        status = request.POST.get('status')

        # Check transaction status
        url = 'https://api.easypay.ug/check_status'  # Replace with the correct EasyPay API URL
        headers = {
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  # Replace with the actual token
            'Content-Type': 'application/json'
        }
        data = {
            'transaction_id': transaction_id
        }

        payment_status = requests.post(url, headers=headers, json=data).json()

        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            if payment_status['status'] == 'success':
                payment.is_paid = True
                payment.save()
                booking = payment.booking
                booking.paid = True
                booking.save()
                return redirect('payment_success')
            else:
                payment.is_paid = False
                payment.save()
                return redirect('payment_failed')
        except Payment.DoesNotExist:
            return redirect('payment_failed')

class InitiatePaymentView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from the request
        booking_id = request.data.get('booking_id')
        phone_number = request.data.get('phone_number')
        amount = request.data.get('amount')

        try:
            # Get the corresponding booking
            booking = Booking.objects.get(id=booking_id)

            # Initialize EasyPayMobileMoney instance
            easypay = EasyPayMobileMoney()

            # Initiate the transaction
            payment_response = easypay.initiate_transaction(
                phone_number=phone_number,
                amount=amount,
                transaction_id=f"BOOKING-{booking.id}",
                description=f"Payment for booking {booking.id}"
            )

            # Check if the payment initiation was successful
            if payment_response.get('status') == 'success':
                # Create a Payment record
                Payment.objects.create(
                    user=request.user,  # Assuming the user is authenticated
                    booking=booking,
                    amount=amount,
                    transaction_id=payment_response.get('transaction_id'),
                    status='pending',
                    payment_method='EasyPay'
                )

                return Response({"message": "Payment initiated successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Payment initiation failed", "details": payment_response.get('message')}, status=status.HTTP_400_BAD_REQUEST)

        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Token views
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        logger.debug(f"User {user.username} successfully logged in.")
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = requests.post(f'{settings.OAUTH2_PROVIDER_URL}/token/refresh/', data={'refresh_token': refresh_token})
            response.raise_for_status()
            data = response.json()
            return Response(data)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return Response({'error': 'Token refresh failed. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
class YourApiView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Your logic here
        return JsonResponse({"message": "Success"})