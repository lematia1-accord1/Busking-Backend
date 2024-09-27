
import requests
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.conf import settings
from django.utils import timezone

# Define the User model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Guest User'),
        ('registered', 'Registered User'),
        ('admin', 'Admin'),
    ]
    
    USER_TYPE_CHOICES = [
        ('merchant', 'Merchant'),
        ('passenger', 'Passenger'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='passenger')

    def is_guest(self):
        return self.role == 'guest'

    def is_registered(self):
        return self.role == 'registered'

    def is_admin(self):
        return self.role == 'admin'


# Define the Merchant model
class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bus_company_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True, null=True) 
    email = models.EmailField(max_length=255, blank=True, null=True)  
    phone_number = models.CharField(max_length=20, blank=True, null=True) 
    address = models.CharField(max_length=255, blank=True, null=True)  
    approved = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.bus_company_name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['is_default'], name='unique_default_merchant', condition=models.Q(is_default=True)),
        ]

# Define the Bus model
class Bus(models.Model):
    name = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=10, unique=True)
    total_seats = models.IntegerField()
    bus_routes = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  

    def __str__(self):
        return self.name

    @property
    def available_seats(self):
        booked_seats = self.bookings.aggregate(total_booked=Sum('seats'))['total_booked'] or 0
        return self.total_seats - booked_seats

    def book_seats(self, number_of_seats):
        if number_of_seats > self.available_seats:
            raise ValidationError("Not enough seats available.")
        # Create a booking instead of modifying the available seats directly

    def clean(self):
        if self.departure_time >= self.arrival_time:
            raise ValidationError("Departure time must be before arrival time.")

    def save(self, *args, **kwargs):
        if self.pk is not None:
            if not self.merchant.approved:
                raise ValidationError("The merchant must be approved before adding buses.")
        else:
            if self.merchant and not self.merchant.approved:
                raise ValidationError("The merchant must be approved before adding buses.")
        
        super().save(*args, **kwargs)

    @property
    def is_full(self):
        return self.available_seats <= 0

    class Meta:
        permissions = [
            ("can_view_bus", "Can view bus"),
            ("can_manage_bus", "Can manage bus"),
            ("can_view_booking_statistics", "Can view booking statistics"),
        ]
        verbose_name_plural = "Buses"


# Define the Booking model
class Booking(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)  # Provide a default value
    bus = models.ForeignKey(Bus, related_name='bookings', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    seats = models.IntegerField()
    booking_date = models.DateTimeField(default=now)
    payment_method = models.CharField(max_length=50, blank=True)
    pickup_location = models.CharField(max_length=255, blank=True)
    pickup_time = models.DateTimeField(blank=True, null=True)
    expected_journey_duration = models.DurationField(null=True, blank=True)
    destination = models.CharField(max_length=255, blank=True)
    is_paid = models.BooleanField(default=False)

    def clean(self):
        if self.pickup_time and self.pickup_time < now():
            raise ValidationError("Pickup time cannot be in the past.")
        if self.seats > self.bus.available_seats:
            raise ValidationError(f"Cannot book {self.seats} seats. Only {self.bus.available_seats} available.")

    def __str__(self):
        return f"Booking by {self.name} for {self.bus.name}"


# Define the Customer model
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# Define the Payment model with direct requests integration
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)  # Link payment to a booking
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True)  # Unique identifier for the payment
    #transaction_id = models.CharField(max_length=255, unique=True, blank=True, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    refunded = models.BooleanField(default=False)
    currency = models.CharField(max_length=10, default='USD')  # Currency type
    is_paid = models.BooleanField(default=False)  # Indicates if payment is completed
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')])
    payment_method = models.CharField(max_length=20, default='EasyPay')

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    def process_payment(self):
        url = 'https://api.easypay.ug/endpoint'  # Replace with the actual EasyPay API URL
        headers = {
            'Authorization': f'Bearer {settings.EASYPAY_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'phone_number': self.booking.phone,
            'amount': float(self.amount),
            'transaction_id': self.transaction_id,
            'description': f'Payment for booking {self.booking.id}'
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            self.status = 'completed'
            self.is_paid = True
            self.save()
        else:
            self.status = 'failed'
            self.save()
            raise ValidationError(f"Payment failed: {response.text}")

    def refund(self):
        if not self.refunded:
            url = f'https://api.easypay.ug/endpoint/refund/{self.transaction_id}'  # Replace with EasyPay refund endpoint
            headers = {
                'Authorization': f'Bearer {settings.EASYPAY_API_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                self.refunded = True
                self.save()
                return True
            else:
                raise ValidationError(f"Refund failed: {response.text}")
        return False

    class Meta:
        ordering = ['-created_at']


class Destination(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}, {self.city}, {self.state}"

class Route(models.Model):
    name = models.CharField(max_length=100)
    start_location = models.CharField(max_length=100)
    end_location = models.CharField(max_length=100)

    def __str__(self):
        return f"Route from {self.start_location} to {self.end_location}"

