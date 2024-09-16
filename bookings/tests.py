from rest_framework import status
from rest_framework.test import APITestCase
from bookings.models import Merchant, Booking, Payment, Bus
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from django.test import TestCase, Client
from django.conf import settings
from django.urls import reverse

User = get_user_model()

class BookingAndPaymentTests(APITestCase):

    def setUp(self):
        """Set up initial data for tests."""
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')
        self.merchant = Merchant.objects.create(user=self.user, bus_company_name='Test Bus Company', approved=True)
        self.bus = Bus.objects.create(
            name='Test Bus',
            merchant=self.merchant,
            license_plate='1234',
            total_seats=50,
            available_seats=50,
            departure_time=timezone.now(),
            arrival_time=timezone.now() + timezone.timedelta(hours=2),
            price=100.00
        )
    
    def create_booking(self, seats=2, payment_method='EasyPay'):
        """Helper function to create a booking with optional seat and payment method."""
        return {
            'bus': self.bus.id,
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'phone': '555-1234',
            'seats': seats,
            'booking_date': timezone.now().isoformat(),
            'payment_method': payment_method,
            'pickup_location': 'Location A',
            'pickup_time': timezone.now().isoformat(),
            'expected_journey_duration': '2 hours',
            'destination': 'Destination B'
        }

    @patch('bookings.models.Payment.refund')  # Mock the refund method
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
            'amount': 200.00,  # Assuming the amount is the total cost of the booking
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
        self.assertIsNone(booking.payment)  # Verify that no payment is associated with the booking

    def test_create_booking_with_invalid_seats(self):
        """Test creating a booking with more seats than available."""
        booking_data = self.create_booking(seats=60)  # Exceeds available seats

        response = self.client.post('/bookings/', booking_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot book', str(response.data))  # Custom error message validation

class CsrfTestCase(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
    
    def test_valid_csrf_token(self):
        response = self.client.post(reverse('your-api-endpoint'), data={}, HTTP_X_CSRFTOKEN='valid-csrf-token')
        self.assertEqual(response.status_code, 200)  # Adjust status code based on expected response

    def test_invalid_csrf_token(self):
        response = self.client.post(reverse('your-api-endpoint'), data={}, HTTP_X_CSRFTOKEN='invalid-csrf-token')
        self.assertEqual(response.status_code, 403)  # CSRF verification should fail




