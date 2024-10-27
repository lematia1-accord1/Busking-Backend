from rest_framework import status
from rest_framework.test import APITestCase
from bookings.models import Merchant, Booking, Payment, Bus
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
import json


User = get_user_model()
class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')


class BookingAndPaymentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='testuser@example.com'
        )
        self.merchant = Merchant.objects.create(
            user=self.user,
            bus_company_name="Test Bus Company",
            approved=True  
        )
        self.bus = Bus.objects.create(
            name="Test Bus",
            license_plate="TEST123",
            total_seats=50,
            price=100.0,
            departure_time="2024-10-03T10:00:00Z",
            arrival_time="2024-10-03T12:00:00Z",
            merchant=self.merchant,  
        )

    
    def test_create_booking_with_invalid_seats(self):

        self.client.login(username='testuser', password='testpassword')

        response = self.client.post('/api/bookings/', {
            'bus': {'id': self.bus.id},  
            'seats': -1  
        })

        self.assertEqual(response.status_code, 400)  

    def create_booking(self, seats=2, payment_method='EasyPay'):
        """Helper function to create a booking with optional seat and payment method."""
        return {
            'bus': self.bus.id,
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'phone': '555-1234',
            'seats': 'seats',
            'booking_date': timezone.now().isoformat(),
            'payment_method': payment_method,
            'pickup_location': 'Location A',
            'pickup_time': timezone.now().isoformat(),
            'expected_journey_duration': '2 hours',
            'destination': 'Destination B'
        }

    @patch('bookings.models.Payment.refund')  
    def test_create_booking_and_payment(self, mock_refund):
        """Test creating a booking and processing a payment."""
        booking_data = self.create_booking(seats=2)

        response = self.client.post('/bookings/', booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']

        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.name, 'John Doe')

        payment_data = {
            'user': self.user.id,
            'booking': booking_id,
            'amount': 200.00,  
            'transaction_id': 'test_transaction_id',
            'timestamp': timezone.now().isoformat(),
            'currency': 'USD',
            'status': 'pending',
            'payment_method': 'EasyPay'
        }

        response = self.client.post('/payments/', payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payment = Payment.objects.get(booking=booking_id)
        self.assertEqual(payment.amount, 200.00)
        self.assertEqual(payment.transaction_id, 'test_transaction_id')

    def test_booking_without_payment(self):
        """Test creating a booking without immediately processing a payment."""
        booking_data = self.create_booking(seats=1)

        response = self.client.post('/bookings/', booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']

        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.name, 'John Doe')
        self.assertIsNone(booking.payment)  

    
class AdminViewTests(TestCase):
    def setUp(self):
        self.normal_user = User.objects.create_user(username='normaluser', password='password')
        self.admin_user = User.objects.create_user(username='adminuser', password='password', is_staff=True)

    def test_admin_access_normal_user(self):
        self.client.login(username='normaluser', password='password')
        response = self.client.get(reverse('admin-dashboard'))  

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_staff_user(self):
        self.client.login(username='adminuser', password='password')
        response = self.client.get(reverse('admin-dashboard'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_access_unauthenticated(self):
        response = self.client.get(reverse('admin-dashboard'))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAuthenticationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='regularuser',
            password='regularpassword'
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            password='adminpassword',
            is_staff=True
        )

    def test_admin_access_regular_user(self):
        self.client.login(username='regularuser', password='regularpassword')
        
        response = self.client.get(reverse('admin_dashboard'))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "You do not have permission to access this page.")
    
    def test_admin_access_admin_user(self):
        self.client.login(username='adminuser', password='adminpassword')
        
        response = self.client.get(reverse('admin_dashboard')) 

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")

class CsrfTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.merchant = Merchant.objects.create(name='Test Merchant', user=self.user, approved=True)

        self.client.login(username='testuser', password='testpassword')

    def test_valid_csrf_token(self):
        response = self.client.get(reverse('bus-create'))

        self.assertIn('csrftoken', response.cookies)

        csrf_token = response.cookies['csrftoken'].value

        response = self.client.post(
            reverse('bus-create'),
            data={
                'name': 'Test Bus',
                'total_seats': 50,
                'license_plate': 'TEST124',
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            },
            HTTP_X_CSRFTOKEN=csrf_token  
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Bus.objects.count(), 1)



class CsrfTestCase(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        self.merchant = Merchant.objects.create(user=self.user, approved=True)
        
    def test_valid_csrf_token(self):
        self.client.login(username=self.username, password=self.password)

        url = reverse('bus-create')
        response = self.client.get(url)

        self.assertIn('csrftoken', response.cookies)

        response = self.client.post(
            url,
            data={
                'name': 'Test Bus',
                'total_seats': 50,
                'license_plate': 'TEST124',
                'merchant': self.merchant.id,  
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            },
            HTTP_X_CSRFTOKEN=response.cookies['csrftoken'].value  
        )

        self.assertEqual(response.status_code, 201)

 
class BusCreateViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)  

        self.merchant = Merchant.objects.create(user=self.user, approved=True)


    def test_valid_csrf_token(self):
        response = self.client.post(
            reverse('bus-create'),
            data={
                'name': 'Test Bus',
                'total_seats': 50,
                'license_plate': 'TEST123',  
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            }
        )
        
        print(response.content) 
        print(response.status_code)  
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_csrf_token(self):
        response = self.client.post(
            reverse('bus-create'),
            data={
                'name': 'Test Bus',
                'total_seats': 50,
                'license_plate': 'TEST124',
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            },
            format='json'
        )



    def test_missing_required_fields(self):
        response = self.client.post(
            reverse('bus-create'),
            data={  
                'total_seats': 50,
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)  
        self.assertIn('license_plate', response.data)  

    def test_non_approved_merchant(self):
        second_user = User.objects.create_user(username='seconduser', password='secondpassword')
        
        unapproved_merchant = Merchant.objects.create(user=second_user, approved=False)
        
        self.assertFalse(unapproved_merchant.approved)

    def test_duplicate_license_plate(self):
        Bus.objects.create(
            name='Existing Bus',
            total_seats=50,
            license_plate='TEST123',
            merchant=self.merchant,
            departure_time='2024-10-01T10:00:00Z',
            arrival_time='2024-10-01T12:00:00Z',
            price=100.00,
            bus_routes='Route A to B'
        )

        response = self.client.post(
            reverse('bus-create'),
            data={
                'name': 'Another Bus',
                'total_seats': 50,
                'license_plate': 'TEST123', 
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T14:00:00Z',
                'arrival_time': '2024-10-01T16:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route B to C',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('license_plate', response.data)  

class MerchantTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')

        self.merchant1 = Merchant.objects.create(user=self.user1)
        self.merchant2 = Merchant.objects.create(user=self.user2)

    def test_create_merchant(self):
        self.assertIsNotNone(self.merchant1)
        self.assertIsNotNone(self.merchant2)

    def test_duplicate_merchant_creation(self):
        with self.assertRaises(Exception):
            Merchant.objects.create(user=self.user1)

class UserAuthViewTests(APITestCase):
    def test_login(self):
        User.objects.create_user(username='testuser', password='testpass')
        
        response = self.client.post(reverse('user-auth'), {
            'username': 'testuser',
            'password': 'testpass',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookBusViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.merchant = Merchant.objects.create(user=self.user, approved=True)

        self.bus = Bus.objects.create(
            name="Test Bus",
            departure_time="2024-10-10T10:00:00Z",
            arrival_time="2024-10-10T12:00:00Z",
            license_plate="ABC123",
            total_seats=60,
            available_seats=60,
            merchant=self.merchant,
            price=10000,
        )

        self.url = reverse('book-bus', kwargs={'bus_id': self.bus.id, 'number_of_seats': 1})

    def test_book_bus_success(self):
        url = reverse('book-bus', kwargs={'bus_id': self.bus.id, 'number_of_seats': 1})
        self.client.force_authenticate(user=self.user)  
        response = self.client.post(url)  

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_book_bus_not_authenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_book_bus_authenticated(self):
        self.client.login(username='testuser', password='testpassword')

        response = self.client.post('/api/buses/{}/book/1/'.format(self.bus.id), {
            'number_of_seats': 1,
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'booking_date': '2024-10-10',
            'payment_method': 'credit_card',
            'pickup_location': 'Pickup Point',
            'pickup_time': '10:00 AM',
            'expected_journey_duration': '2 hours',
            'destination': 'Final Destination',
        })

        self.assertEqual(response.status_code, 201)  


class BookBusViewTest(TestCase):

    def setUp(self):
        self.merchant = Merchant.objects.create(
            name="Test Merchant",
            approved=True  
        )

        self.bus = Bus.objects.create(
            name="Test Bus",
            departure_time="2024-12-01T10:00:00Z",
            arrival_time="2024-12-01T12:00:00Z",
            merchant=self.merchant,
            license_plate="TEST123",
            total_seats=60,  
            available_seats=60,  
            price=50000
        )

    def test_book_bus_successful(self):
        response = self.client.post('/api/buses/1/book/3/', {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '123456789',
            'booking_date': '2024-12-01',
            'payment_method': 'credit_card',
            'pickup_location': 'Station A',
            'pickup_time': '2024-12-01T09:00:00Z',
            'expected_journey_duration': '2 hours',
            'destination': 'City B',
        })

        self.assertEqual(response.status_code, 302)  

    def test_book_bus_insufficient_seats(self):
        self.bus.available_seats = 0  
        self.bus.save()  
        
        response = self.client.post('/api/buses/1/book/1/', {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '987654321',
            'booking_date': '2024-12-01',
            'payment_method': 'credit_card',
            'pickup_location': 'Station A',
            'pickup_time': '2024-12-01T09:00:00Z',
            'expected_journey_duration': '2 hours',
            'destination': 'City B',
        })

        self.assertEqual(response.status_code, 400)  


class ChangePasswordViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='oldpassword123'
        )
        self.url = reverse('change-password') 
        self.client.login(username='testuser', password='oldpassword123')

    def test_unauthenticated_user(self):
        response = self.client.post('/api/change_password/', {}, format='json')  

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



    def test_missing_password_fields(self):
        """Test if missing password fields return the appropriate error."""
        data = json.dumps({
            'old_password': '',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        response = self.client.post(self.url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'All password fields (old_password, new_password1, new_password2) are required.'})

    def test_new_passwords_do_not_match(self):
        """Test if new passwords mismatch returns an error."""
        data = json.dumps({
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword123',
            'new_password2': 'differentpassword'
        })
        response = self.client.post(self.url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'New passwords do not match.'})

    def test_new_password_too_short(self):
        """Test if new password is too short."""
        data = json.dumps({
            'old_password': 'oldpassword123',
            'new_password1': 'short',
            'new_password2': 'short'
        })
        response = self.client.post(self.url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'error': 'New password must be at least 8 characters long.'})

    def test_successful_password_change(self):
        """Test successful password change."""
        data = json.dumps({
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        response = self.client.post(self.url, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': 'Password changed successfully'})
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
