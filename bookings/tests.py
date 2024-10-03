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

User = get_user_model()
class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')


class BookingAndPaymentTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='testuser@example.com'
        )
        # Create an approved merchant linked to the user
        self.merchant = Merchant.objects.create(
            user=self.user,
            bus_company_name="Test Bus Company",
            approved=True  # Ensure the merchant is approved
        )
        # Create a bus associated with the approved merchant
        self.bus = Bus.objects.create(
            name="Test Bus",
            license_plate="TEST123",
            total_seats=50,
            price=100.0,
            departure_time="2024-10-03T10:00:00Z",
            arrival_time="2024-10-03T12:00:00Z",
            merchant=self.merchant,  # Use the approved merchant
        )

    def test_create_booking_with_invalid_seats(self):
        response = self.client.post('/api/bookings/', {
            'bus': {'id': 1},  # Valid bus ID
            'seats': -1  # Invalid number of seats
        })
        self.assertEqual(response.status_code, 400)  # Expect a 400 Bad Request

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

        # Create a booking
        response = self.client.post('/bookings/', booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']

        # Verify the booking was created
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.name, 'John Doe')

        # Process a payment
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

        # Verify the payment was created and linked to the booking
        payment = Payment.objects.get(booking=booking_id)
        self.assertEqual(payment.amount, 200.00)
        self.assertEqual(payment.transaction_id, 'test_transaction_id')

    def test_booking_without_payment(self):
        """Test creating a booking without immediately processing a payment."""
        booking_data = self.create_booking(seats=1)

        # Create a booking
        response = self.client.post('/bookings/', booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        booking_id = response.data['id']

        # Verify the booking was created
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.name, 'John Doe')
        self.assertIsNone(booking.payment)  

    
class AdminViewTests(TestCase):
    def setUp(self):
        # Create a normal user
        self.normal_user = User.objects.create_user(username='normaluser', password='password')
        # Create a staff user (admin)
        self.admin_user = User.objects.create_user(username='adminuser', password='password', is_staff=True)

    def test_admin_access_normal_user(self):
        # Log in the normal user
        self.client.login(username='normaluser', password='password')
        response = self.client.get(reverse('admin-dashboard'))  

        # Expect a 403 Forbidden if the user is not an admin
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_access_staff_user(self):
        # Log in the staff user
        self.client.login(username='adminuser', password='password')
        response = self.client.get(reverse('admin-dashboard'))

        # Staff user should have access
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_access_unauthenticated(self):
        # Try accessing the admin view without logging in
        response = self.client.get(reverse('admin-dashboard'))

        # Unauthenticated users should be forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminAuthenticationTest(TestCase):
    def setUp(self):
        # Create a regular user (staff but not superuser) and a superuser
        self.regular_user = User.objects.create_user(username='user', password='pass', is_staff=True, is_superuser=False)
        self.super_user = User.objects.create_superuser(username='admin', password='pass')

    def test_admin_access_regular_user(self):
        # Log in as a regular staff user (not a superuser)
        self.client.login(username='user', password='pass')

        # Try to access the admin panel
        response = self.client.get(reverse('admin:index'))

        # Check if the response is a redirect (302) to the login page
        self.assertEqual(response.status_code, 302)

        # Verify that the redirect URL is the login page
        login_url = f"{reverse('login')}?next={reverse('admin:index')}"
        self.assertEqual(response.url, login_url)


class CsrfTestCase(APITestCase):
    def setUp(self):
        # Create a user and a merchant for testing
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.merchant = Merchant.objects.create(name='Test Merchant', user=self.user, approved=True)

        # Log in the user
        self.client.login(username='testuser', password='testpassword')

    def test_valid_csrf_token(self):
        # Make a GET request to get the CSRF token
        response = self.client.get(reverse('bus-create'))

        # Check if the CSRF token is set in cookies
        self.assertIn('csrftoken', response.cookies)

        # Get the CSRF token
        csrf_token = response.cookies['csrftoken'].value

        # Now make a valid POST request with the CSRF token
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
            HTTP_X_CSRFTOKEN=csrf_token  # Use the correct CSRF token
        )

        # Assert that the response is 201 Created
        self.assertEqual(response.status_code, 201)

        # Check that the bus was created
        self.assertEqual(Bus.objects.count(), 1)



class CsrfTestCase(TestCase):
    def setUp(self):
        # Create a user and merchant for the test
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        # Create an approved merchant for the user
        self.merchant = Merchant.objects.create(user=self.user, approved=True)
        
    def test_valid_csrf_token(self):
        # Log in the user
        self.client.login(username=self.username, password=self.password)

        # Get the CSRF token via GET request
        url = reverse('bus-create')
        response = self.client.get(url)

        # Ensure CSRF token is in cookies
        self.assertIn('csrftoken', response.cookies)

        # Perform POST request with valid CSRF token
        response = self.client.post(
            url,
            data={
                'name': 'Test Bus',
                'total_seats': 50,
                'license_plate': 'TEST124',
                'merchant': self.merchant.id,  # Use the created merchant
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            },
            HTTP_X_CSRFTOKEN=response.cookies['csrftoken'].value  # Use valid CSRF token
        )

        # Ensure response status is 201 Created
        self.assertEqual(response.status_code, 201)

 
class BusCreateViewTests(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)  

        # Create a merchant instance for testing
        self.merchant = Merchant.objects.create(user=self.user, approved=True)


    def test_valid_csrf_token(self):
        # If CSRF token is required, it will usually be done in views
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
        
        print(response.content)  # Debugging output
        print(response.status_code)  # Debugging output
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
            data={  # Missing required fields like name, total_seats, and license_plate
                'total_seats': 50,
                'merchant': self.merchant.id,
                'departure_time': '2024-10-01T10:00:00Z',
                'arrival_time': '2024-10-01T12:00:00Z',
                'price': 100.00,
                'bus_routes': 'Route A to B',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)  # Check for specific error messages
        self.assertIn('license_plate', response.data)  # Check for specific error messages

    def test_non_approved_merchant(self):
        # Create a second user for the non-approved merchant
        second_user = User.objects.create_user(username='seconduser', password='secondpassword')
        
        # Create a non-approved merchant for the second user
        unapproved_merchant = Merchant.objects.create(user=second_user, approved=False)
        
        # Here, you can add logic to test the scenario for the non-approved merchant
        self.assertFalse(unapproved_merchant.approved)

    def test_duplicate_license_plate(self):
        # Create the first bus
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

        # Attempt to create a duplicate bus
        response = self.client.post(
            reverse('bus-create'),
            data={
                'name': 'Another Bus',
                'total_seats': 50,
                'license_plate': 'TEST123',  # Duplicate license plate
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
        # Create unique users for testing
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')

        # Create merchants for the unique users
        self.merchant1 = Merchant.objects.create(user=self.user1)
        self.merchant2 = Merchant.objects.create(user=self.user2)  # Different user

    def test_create_merchant(self):
        # Test that a merchant can be created
        self.assertIsNotNone(self.merchant1)
        self.assertIsNotNone(self.merchant2)

    def test_duplicate_merchant_creation(self):
        # Attempt to create a second merchant for user1 should raise IntegrityError
        with self.assertRaises(Exception):
            Merchant.objects.create(user=self.user1)

class UserAuthViewTests(APITestCase):
    def test_login(self):
        # Create a test user
        User.objects.create_user(username='testuser', password='testpass')
        
        # Attempt to login
        response = self.client.post(reverse('user-auth'), {
            'username': 'testuser',
            'password': 'testpass',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
