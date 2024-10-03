import logging
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
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
from rest_framework.views import APIView
from .easypay_mobile_money import EasyPayMobileMoney
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from .models import Destination, Route
from rest_framework.generics import ListAPIView, RetrieveAPIView 
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse,HttpResponse
from django.views import View
import json
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
import re
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import HttpResponseForbidden
from django.db import IntegrityError
from rest_framework import serializers  

from .models import Bus, Merchant, Booking, Customer, Payment
from .serializers import UserSerializer, BusSerializer, BookingSerializer,CustomTokenObtainPairSerializer, DestinationSerializer, MerchantSerializer, CustomerSerializer, DestinationSerializer, RouteSerializer
from .forms import BookingForm


# User model
User = get_user_model()

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Welcome to the home page!")

class AdminView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You need to be logged in to access this page.")
        
        if not request.user.is_staff:  
            return HttpResponseForbidden("You do not have permission to access this page.")
        
        # Your logic here (for authorized admin users)
        return HttpResponse("Admin Dashboard")


def clean_request_data(data):
    # Implement your data cleaning logic here
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned_data[key] = value.strip() 
        else:
            cleaned_data[key] = value
    return cleaned_data

class CSRFTokenView(APIView):
    def get(self, request, *args, **kwargs):
        csrf_token = get_token(request)
        return JsonResponse({'csrfToken': csrf_token})

class CsrfTestView(APIView):
    @ensure_csrf_cookie  
    def get(self, request):
        return Response({'status': 'CSRF cookie set'})


def csrf_failure_view(request, reason=""):
    return JsonResponse({'error': 'CSRF verification failed. Please try again.'}, status=403)

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


class UserDetailView(generics.RetrieveAPIView): 
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        user = self.get_object() 
        
        # Allow access to the logged-in user's details or an admin
        if user.id != request.user.id and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to access this user.")

        # Return user details
        return Response({
            'username': user.username,
            'email': user.email,
            'other_details': user.other_field  
        })

    
#User registration view (POST)
@method_decorator(csrf_protect, name='dispatch')
class RegisterView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)

            user = User.objects.create_user(username=username, password=password)
            return JsonResponse({'message': 'User registered successfully'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)


# User profile view (GET)
@login_required
def profile_json_view(request):
    user_data = {
        "username": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name
    }
    return JsonResponse(user_data, status=200)

# Password Change API
@method_decorator(csrf_protect, name='dispatch')
class ChangePasswordView(View):
    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Password changed successfully'}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Profile updated successfully'}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)

    # If the request method is GET, return the user's current data
    current_data = {
        'username': request.user.username,
        'email': request.user.email,
        # Add any other fields you want to include
    }
    return JsonResponse(current_data, status=200)


# For authenticated users to create buses
@method_decorator(csrf_protect, name='dispatch')  
@method_decorator(ensure_csrf_cookie, name='dispatch')
class BusCreateView(generics.CreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        merchant = get_object_or_404(Merchant, user=self.request.user)

        if merchant.approved:
            serializer.save(merchant=merchant)
        else:
            raise ValidationError("Merchant must be approved to add buses.")


# For all users to list buses
class BusListView(generics.ListCreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.AllowAny]  

    def get_queryset(self):
        # List only buses from approved merchants
        return Bus.objects.filter(merchant__approved=True)

    def perform_create(self, serializer):
        # Ensure the merchant is approved before allowing bus creation
        merchant_id = self.request.data.get('merchant') 
        try:
            merchant = Merchant.objects.get(id=merchant_id)
            if not merchant.approved:
                return Response({'detail': 'Merchant is not approved.'}, status=status.HTTP_403_FORBIDDEN)
        except Merchant.DoesNotExist:
            return Response({'detail': 'Merchant does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Save the bus if the merchant is approved
        serializer.save()
    
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
        # Allow access only to buses associated with the user's approved merchants
        return Bus.objects.filter(merchant__user=self.request.user, merchant__approved=True)

    def get(self, request, *args, **kwargs):
        bus = self.get_object() 
        logger.debug(f"Requesting bus ID: {bus.id} for user ID: {request.user.id}")

        # Check if the bus is associated with the user's approved merchant
        if bus.merchant.user != request.user:
            logger.debug(f"Bus merchant ID: {bus.merchant.user.id} does not match user ID: {request.user.id}")
            raise NotFound("You do not have permission to access this bus.")

        # Return the bus details
        serializer = self.get_serializer(bus)
        return Response(serializer.data)


    def perform_update(self, serializer):
        # Ensure that the user is the merchant associated with the bus
        bus = self.get_object()
        if bus.merchant.user != self.request.user:
            raise NotFound("You do not have permission to update this bus.")

        # Update the bus
        serializer.save()

    def perform_destroy(self, instance):
        # Ensure that the user is the merchant associated with the bus
        if instance.merchant.user != self.request.user:
            raise NotFound("You do not have permission to delete this bus.")

        # Delete the bus
        instance.delete()

class BookBusView(APIView):
    def post(self, request, bus_id, number_of_seats):
        # Get the bus object or return a 404 if not found
        bus = get_object_or_404(Bus, id=bus_id)

        # Validate the number of seats
        if number_of_seats > bus.available_seats:
            return Response({'error': 'Not enough seats available.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a booking instance
        booking = Booking(user=request.user, bus=bus, seats_booked=number_of_seats)
        booking.save()  # Save the booking to the database

        # Update the available seats on the bus
        bus.available_seats -= number_of_seats
        bus.save()  # Save the updated bus

        return Response({'message': 'Booking successful.', 'booking_id': booking.id}, status=status.HTTP_201_CREATED)

def view_available_buses(request):
    """View to retrieve a list of available buses."""
    buses = Bus.objects.filter(merchant__approved=True)
    data = [{
        'id': bus.id,
        'name': bus.name,
        'departure_time': bus.departure_time,
        'arrival_time': bus.arrival_time,
        'price': bus.price,
        'total_seats': bus.total_seats,
        'available_seats': bus.available_seats,
        'bus_routes': bus.bus_routes,  
    } for bus in buses]
    return JsonResponse(data, safe=False)


# Booking Views
class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Booking.objects.all()

    def perform_create(self, serializer):
        # Extract the bus data and requested seats from the request data
        bus_data = self.request.data.get('bus')
        seats_requested = self.request.data.get('seats')

        # Validate bus data
        if not bus_data or not isinstance(bus_data, dict) or 'id' not in bus_data:
            # Return a 400 error if the bus data is not provided correctly
            raise serializers.ValidationError({'error': 'Bus data is required.'})

        bus_id = bus_data['id']  # Get the bus ID from the bus data

        try:
            # Fetch the bus object
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            # Raise a validation error if the bus does not exist
            raise serializers.ValidationError({'error': 'Bus not found.'})

        # Validate the seats_requested
        if seats_requested is None:
            raise serializers.ValidationError({'error': 'Seats requested is required.'})

        try:
            # Convert seats_requested to an integer
            seats_requested = int(seats_requested)
        except (ValueError, TypeError):
            raise serializers.ValidationError({'error': 'Invalid number of seats requested.'})

        # Check if requested seats exceed available seats
        if seats_requested <= 0:
            raise serializers.ValidationError({'error': 'The number of seats must be greater than zero.'})

        if seats_requested > bus.available_seats:
            raise serializers.ValidationError({'error': 'Not enough seats available.'})

        # Save the booking if all checks pass
        serializer.save(bus=bus, seats=seats_requested)



class BookingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


@login_required
@require_POST
def book_ticket(request, bus_id):
    """View to book a ticket for a specific bus."""
    bus = get_object_or_404(Bus, id=bus_id)

    if 'seats' not in request.POST:
        return JsonResponse({'error': 'Number of seats is required.'}, status=400)

    form = BookingForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid form data.'}, status=400)

    seats = int(request.POST['seats'])
    if seats <= bus.available_seats:
        booking = Booking(user=request.user, bus=bus, seats_booked=seats)
        booking.save()

        bus.available_seats -= seats
        bus.save()

        return JsonResponse({
            'message': 'Booking successful.',
            'booking_id': booking.id,
        }, status=201)
    else:
        return JsonResponse({'error': 'Not enough seats available.'}, status=400)

    # If all checks fail (which shouldn't happen due to the use of get_object_or_404)
    return JsonResponse({'error': 'Invalid request.'}, status=400)


@login_required
def payment_process(request, booking_id):
    """View to process payment for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id)

    # Create a response with booking details for payment processing
    data = {
        'booking_id': booking.id,
        'bus_name': booking.bus.name,
        'departure_time': booking.bus.departure_time,
        'arrival_time': booking.bus.arrival_time,
        'price': booking.bus.price,
        'seats_booked': booking.seats_booked,
        'user_email': booking.user.email,
    }
    return JsonResponse(data, status=200)


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
    """View to retrieve the booking history for the logged-in user."""
    bookings = Booking.objects.filter(user=request.user).select_related('bus')

    # Prepare the booking data for JSON response
    booking_data = [
        {
            'booking_id': booking.id,
            'bus_name': booking.bus.name,
            'departure_time': booking.bus.departure_time,
            'arrival_time': booking.bus.arrival_time,
            'price': booking.bus.price,
            'seats_booked': booking.seats_booked,
            'booking_date': booking.created_at,  
        }
        for booking in bookings
    ]

    return JsonResponse({'bookings': booking_data}, status=200)

@login_required
def cancel_booking(request, booking_id):
    # Ensure this view only responds to DELETE requests
    if request.method == 'DELETE':
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)
        bus = booking.bus
        bus.available_seats += booking.seats_booked
        bus.save()
        booking.delete()
        return JsonResponse({'message': 'Booking canceled successfully'}, status=204)  

    return JsonResponse({'error': 'Method not allowed'}, status=405) 

# Admin Views
@staff_member_required
def manage_buses(request):
    """View to retrieve all buses for management."""
    buses = Bus.objects.all().values('id', 'name', 'departure_time', 'arrival_time', 'price', 'total_seats', 'available_seats')
    
    return JsonResponse({'buses': list(buses)}, status=200)

@staff_member_required
def booking_stats(request):
    """View to retrieve booking statistics grouped by bus."""
    from django.db.models import Count
    
    stats = Booking.objects.values('bus__name').annotate(total=Count('id'))
    
    return JsonResponse({'stats': list(stats)}, status=200)


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
class ApproveMerchantView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, merchant_id, *args, **kwargs):
        merchant_to_approve = get_object_or_404(Merchant, id=merchant_id)

        if merchant_to_approve.is_default:
            return Response({"detail": "Cannot approve a default merchant."}, status=400)

        # Logic to approve the merchant
        merchant_to_approve.approved = True
        merchant_to_approve.save()

        return Response({"detail": "Merchant approved successfully."}, status=200)
    
def create_merchant_for_user(user):
    # Check if the user already has a merchant
    if Merchant.objects.filter(user=user).exists():
        raise IntegrityError("This user already has a Merchant.")
    # Proceed to create the Merchant
    return Merchant.objects.create(user=user)


class MerchantDetailView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, pk):
        # Log the user and merchant request
        logger.info(f"User: {request.user} requested merchant {pk}")
        
        # Clean the pk (if needed, e.g., removing unwanted characters)
        cleaned_pk = re.sub(r'\s+', '', str(pk))  

        # Retrieve the merchant details using the cleaned pk
        merchant = get_object_or_404(Merchant, pk=cleaned_pk)

        # Return the merchant details
        return Response({
            'id': merchant.id,
            'name': merchant.name,
            'email': merchant.email,
            'bus_company_name': merchant.bus_company_name,
            'phone_number': merchant.phone_number,
            'address': merchant.address,
            'approved': merchant.approved,
        })

    
class MerchantListView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request):
        merchants = Merchant.objects.all()
        serializer = MerchantSerializer(merchants, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = MerchantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MerchantCreateView(APIView):
    def post(self, request):
        # Lookup user by username
        username = request.data.get('user')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user already has a Merchant
        if Merchant.objects.filter(user=user).exists():
            raise ValidationError("This user already has a Merchant.")

        # Update the request data to include the user ID
        request.data['user'] = user.id

        serializer = MerchantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        url = 'https://api.easypay.ug/endpoint'  
        headers = {
            'Authorization': f'Bearer {settings.EASYPAY_ACCESS_TOKEN}',  
            'Content-Type': 'application/json'
        }
        data = {
            'amount': booking.calculate_total_price(),  
            'currency': 'UGX',  
            'reference': booking.id
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()  
            payment_data = response.json()
            logger.info(f"Payment initiated successfully. Response: {payment_data}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during payment initiation: {str(e)}")
            return JsonResponse({'error': 'Payment initiation failed. Please try again.'}, status=500)

        return redirect('booking_success', booking_id=booking.id)
    
@method_decorator(csrf_exempt, name='dispatch')
class EasyPayCallbackView(View):
    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get('transaction_id')
        status = request.POST.get('status')

        # Check transaction status
        url = 'https://api.easypay.ug/check_status'  
        headers = {
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN',  
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
                    user=request.user,  
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


class UserAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Clean the request data to remove unwanted characters
        cleaned_data = self.clean_request_data(request.data)

        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Authenticate the user
        user = authenticate(username=username, password=password)

        if user is not None:
            # Generate tokens for the authenticated user
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            }, status=200)

        return Response({'detail': 'Invalid credentials'}, status=400)
    
    def get(self, request):
        # Return a simple JSON response or a message indicating that this is a login endpoint
        return JsonResponse({'message': 'Please use POST to log in.'}, status=200)
    



    def clean_request_data(self, data):
        # Sanitize input data to remove any newline or whitespace characters
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_data[key] = re.sub(r'\s+', '', value)  
            else:
                cleaned_data[key] = value
        return cleaned_data


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Logout logic (blacklist the token if you are using simplejwt)
            token = request.data.get('token') 
            if token:
                # You might need to implement token blacklisting logic here
                BlacklistedToken.objects.create(token=token) 
            return Response({"detail": "Successfully logged out."}, status=205)  
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

        
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            
            # Access the user object directly from the serializer
            user = serializer.user
            
            # Logging user login
            logger.debug(f"User {user.username} successfully logged in.")
            
            # Return the validated data (tokens + additional user info)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during token obtain: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

class YourApiView(View):
    @method_decorator(csrf_protect)  
    def post(self, request):
        # Your logic here
        return JsonResponse({"message": "Success"})

    
class CreateDestinationView(generics.CreateAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

class DestinationDetailView(generics.RetrieveAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

class DestinationListView(generics.ListAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

class RouteListView(ListAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class RouteDetailView(RetrieveAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class RouteCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def post(self, request):
        serializer = RouteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


