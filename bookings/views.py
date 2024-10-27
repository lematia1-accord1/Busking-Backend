import logging
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
import requests
from rest_framework.views import APIView
from .easypay_mobile_money import EasyPayMobileMoney
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from .models import Destination, Route
from rest_framework.generics import ListAPIView, RetrieveAPIView 
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse,HttpResponse
import json
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
import re
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db import IntegrityError 
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Bus, Merchant, Booking, Customer, Payment
from .serializers import UserSerializer, BusSerializer, BookingSerializer,CustomTokenObtainPairSerializer, DestinationSerializer, MerchantSerializer, CustomerSerializer, DestinationSerializer, RouteSerializer


User = get_user_model()

logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Welcome to the home page!")

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
        
        if user.id != request.user.id and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to access this user.")

        return Response({
            'username': user.username,
            'email': user.email,
            'other_details': user.other_field  
        })

    
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

        
    def validate_input(self, username, password):
        """Helper method to validate input data."""
        if not username or not password:
            return 'Username and password are required.'
        if len(username) < 3:
            return 'Username must be at least 3 characters long.'
        if len(password) < 8:
            return 'Password must be at least 8 characters long.'
        return None


@api_view(['GET']) 
@permission_classes([IsAuthenticated])  
def profile_json_view(request):
    user_data = {
        "username": request.user.username,
        "email": request.user.email,
        "first_name": request.user.first_name,
        "last_name": request.user.last_name
    }
    return JsonResponse(user_data, status=200)


class ChangePasswordView(APIView):

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        old_password = data.get('old_password')
        new_password1 = data.get('new_password1')
        new_password2 = data.get('new_password2')

        errors = self.validate_input(old_password, new_password1, new_password2)
        if errors:
            return Response({'error': errors}, status=status.HTTP_400_BAD_REQUEST)

        form = PasswordChangeForm(user=request.user, data={
            'old_password': old_password,
            'new_password1': new_password1,
            'new_password2': new_password2
        })

        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': form.errors}, status=status.HTTP_400_BAD_REQUEST)

    def validate_input(self, old_password, new_password1, new_password2):
        if not all([old_password, new_password1, new_password2]):
            return 'All password fields (old_password, new_password1, new_password2) are required.'
        if new_password1 != new_password2:
            return 'New passwords do not match.'
        if len(new_password1) < 8:
            return 'New password must be at least 8 characters long.'
        return None


class EditProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



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


class BusListView(generics.ListCreateAPIView):
    serializer_class = BusSerializer
    permission_classes = [permissions.AllowAny]  

    def get_queryset(self):
        return Bus.objects.filter(merchant__approved=True)

    def perform_create(self, serializer):
        merchant_id = self.request.data.get('merchant') 
        try:
            merchant = Merchant.objects.get(id=merchant_id)
            if not merchant.approved:
                return Response({'detail': 'Merchant is not approved.'}, status=status.HTTP_403_FORBIDDEN)
        except Merchant.DoesNotExist:
            return Response({'detail': 'Merchant does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
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
        return Bus.objects.filter(merchant__approved=True)

    def get(self, request, *args, **kwargs):
        try:
            bus = self.get_object()
            logger.debug(f"Requesting bus ID: {bus.id} for user ID: {request.user.id}")
        except Bus.DoesNotExist:
            logger.debug(f"Bus with ID {kwargs['pk']} not found for user {request.user.id}")
            raise NotFound("Bus not found.")

        serializer = self.get_serializer(bus)
        return Response(serializer.data)

    def perform_update(self, serializer):
        bus = self.get_object()
        if bus.merchant.user != self.request.user:
            raise PermissionDenied("You do not have permission to update this bus.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.merchant.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this bus.")
        instance.delete()
        return Response({"detail": "Bus deleted successfully."}, status=status.HTTP_200_OK)


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


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        queryset = Booking.objects.all()
        logger.debug(f"Total Bookings Found: {queryset.count()}")
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        bus_id = self.request.data.get('bus', {}).get('id')
        seats_requested = self.request.data.get('seats')

        if not bus_id or not seats_requested:
            logger.error("Bus data and seats requested are required.")
            raise serializers.ValidationError({'error': 'Bus data and seats requested are required.'})

        try:
            bus = Bus.objects.select_for_update().get(id=bus_id)
            seats_requested = int(seats_requested)

            if seats_requested <= 0 or seats_requested > bus.available_seats:
                logger.error("Invalid or insufficient seats requested.")
                raise serializers.ValidationError({'error': 'Invalid or insufficient seats.'})
        except (Bus.DoesNotExist, ValueError) as e:
            logger.error(f"Bus not found or invalid seat data: {e}")
            raise serializers.ValidationError({'error': 'Bus not found or invalid seat data.'})

        bus.available_seats -= seats_requested
        bus.save()

        logger.info(f"Creating booking for user {self.request.user} for bus {bus_id} with {seats_requested} seats.")
        serializer.save(bus=bus, seats_booked=seats_requested, user=self.request.user)  

class BookingRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"detail": "Booking cancelled successfully."}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@login_required
def payment_process(request, booking_id):
    """View to process payment for a specific booking."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    send_mail(
        'Booking Confirmation',
        f'Your booking for {booking.bus.name} is confirmed.',
        None,
        [booking.user.email],
        fail_silently=False,
    )

    return Response({"detail": "Booking confirmed successfully."}, status=status.HTTP_200_OK)



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


class ApproveMerchantView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser] 

    def patch(self, request, merchant_id, *args, **kwargs):
        merchant_to_approve = get_object_or_404(Merchant, id=merchant_id)

        if merchant_to_approve.is_default:
            return Response({"detail": "Cannot approve a default merchant."}, status=status.HTTP_400_BAD_REQUEST)

        merchant_to_approve.approved = True
        merchant_to_approve.save()

        buses_to_approve = Bus.objects.filter(merchant=merchant_to_approve)
        buses_to_approve.update(approved=True)

        return Response({"detail": f"Merchant and {buses_to_approve.count()} buses approved successfully."}, status=status.HTTP_200_OK)

    
def create_merchant_for_user(user):
    if Merchant.objects.filter(user=user).exists():
        raise IntegrityError("This user already has a Merchant.")
    return Merchant.objects.create(user=user)


class MerchantDetailView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request, pk):
        logger.info(f"User: {request.user} requested merchant {pk}")
        
        cleaned_pk = re.sub(r'\s+', '', str(pk))  

        merchant = get_object_or_404(Merchant, pk=cleaned_pk)

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
        username = request.data.get('user')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if Merchant.objects.filter(user=user).exists():
            raise ValidationError("This user already has a Merchant.")

        request.data['user'] = user.id

        serializer = MerchantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

class BookBusView(View):
    permission_classes = [IsAuthenticated]

    def post(self, request, bus_id, number_of_seats, *args, **kwargs):
        logger.debug(f"Request data: {request.body}")
        logger.debug(f"Bus ID: {bus_id}, Number of Seats: {number_of_seats}")

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        bus = get_object_or_404(Bus, id=bus_id)
        logger.debug(f"Available seats for bus {bus.id}: {bus.available_seats}")

        if number_of_seats > bus.available_seats:
            return JsonResponse({'error': 'Not enough seats available.'}, status=400)
        
        try:
            pickup_time_str = data.get('pickup_time')
            booking_date_str = data.get('booking_date')
            pickup_time = datetime.strptime(pickup_time_str, '%I:%M %p').time()
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            pickup_datetime = datetime.combine(booking_date, pickup_time)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid pickup_time or booking_date format.'}, status=400)

        try:
            booking, payment_response = create_booking(bus_id, number_of_seats, request.user, data)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=500)

        return JsonResponse({
            'message': 'Booking successful',
            'booking_id': booking.id,
            'pickup_datetime': pickup_datetime.isoformat(),
            'payment': payment_response  
        }, status=201)


def create_booking(bus_id, number_of_seats, user, data):
    bus = get_object_or_404(Bus, id=bus_id)

    try:
        bus.book_seats(number_of_seats)  
    except ValidationError as e:
        raise ValueError(str(e))

    booking = Booking.objects.create(
        user=user,
        bus=bus,
        seats_booked=number_of_seats,
        pickup_time=data.get('pickup_time'),
        booking_date=data.get('booking_date'),
        pickup_location=data.get('pickup_location'),
        expected_journey_duration=data.get('expected_journey_duration'),
        destination=data.get('destination'),
    )

    payment_data = {
        'amount': booking.calculate_total_price(),  
        'currency': 'UGX',
        'reference': booking.id
    }
    headers = {
        'Authorization': f'Bearer {settings.EASYPAY_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post('https://api.easypay.ug/endpoint', headers=headers, json=payment_data)
        response.raise_for_status()
        payment_response = response.json()
        logger.info(f"Payment initiated successfully for Booking ID: {booking.id}, Response: {payment_response}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during payment initiation for Booking ID: {booking.id}: {str(e)}")
        raise ValueError("Payment initiation failed. Please try again.")

    return booking, payment_response

    
@method_decorator(csrf_exempt, name='dispatch')
class EasyPayCallbackView(View):
    def post(self, request, *args, **kwargs):
        transaction_id = request.POST.get('transaction_id')
        status = request.POST.get('status')

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
        
        booking_id = request.data.get('booking_id')
        phone_number = request.data.get('phone_number')
        amount = request.data.get('amount')

        try:
            
            booking = Booking.objects.get(id=booking_id)

            easypay = EasyPayMobileMoney()

            payment_response = easypay.initiate_transaction(
                phone_number=phone_number,
                amount=amount,
                transaction_id=f"BOOKING-{booking.id}",
                description=f"Payment for booking {booking.id}"
            )

            
            if payment_response.get('status') == 'success':
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

    @method_decorator(ensure_csrf_cookie)  
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            csrf_token = get_token(request)
            
            response_data = {
                'message': 'Login successful',
                'refresh': str(refresh), 
                'access': str(refresh.access_token), 
            }
            response = Response(response_data, status=status.HTTP_200_OK)
            response.set_cookie('csrftoken', csrf_token) 
            return response
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request):
        return JsonResponse({'message': 'Please use POST to log in.'}, status=200)

    
    def clean_request_data(self, data):
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_data[key] = re.sub(r'\s+', '', value)  
            else:
                cleaned_data[key] = value
        return cleaned_data


class UserLogoutView(APIView):
    permission_classes = [AllowAny]


    def post(self, request):
        try:
            token = request.data.get('token') 
            if token:
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
            
            user = serializer.user
            
            logger.debug(f"User {user.username} successfully logged in.")
            
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


