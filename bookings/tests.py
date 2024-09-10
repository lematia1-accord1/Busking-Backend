from rest_framework import status
from rest_framework.test import APITestCase
from bookings.models import Merchant
from django.contrib.auth import get_user_model  # Corrected import for User model

User = get_user_model()

class SignupTests(APITestCase):

    def test_successful_signup(self):
        """Test successful user signup."""
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post('/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testuser')

    def test_signup_with_existing_username(self):
        """Test signup with an existing username."""
        User.objects.create_user(username='existinguser', password='password123')
        data = {
            'username': 'existinguser',
            'password': 'testpassword',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post('/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_signup_with_invalid_email(self):
        """Test signup with an invalid email."""
        data = {
            'username': 'testuser',
            'password': 'testpassword',
            'email': 'invalid_email',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post('/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_signup_as_merchant(self):
        """Test successful signup as a merchant."""
        data = {
            'username': 'testmerchant',
            'password': 'testpassword',
            'email': 'merchant@example.com',
            'first_name': 'Test',
            'last_name': 'Merchant',
            'user_type': 'merchant',  # Corrected field for user type
            'bus_company_name': 'Test Bus Company'
        }
        response = self.client.post('/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'testmerchant')
        
        # Check if the Merchant was created and associated correctly
        merchant = Merchant.objects.get(user__username='testmerchant')
        self.assertEqual(merchant.bus_company_name, 'Test Bus Company')
