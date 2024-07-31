# models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

class User(AbstractUser):
    # Add additional fields if needed
    
    user_type = models.CharField(max_length=10, choices=(
        ('merchant', 'Merchant'),
        ('passenger', 'Passenger'),
    ), default='passenger')
    

class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bus_company_name = models.CharField(max_length=255)

    def __str__(self):
        return self.bus_company_name
    


class Bus(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=10, unique=True)

    name = models.CharField(max_length=100)
    total_seats = models.IntegerField()
    available_seats = models.IntegerField(default=0)

    # Removed hardcoded destinations
    # Instead, we'll store destinations as a list of strings in a TextField
    destinations = models.TextField(blank=True)

    # Removed hardcoded travel_routes
    # Instead, we'll store routes as a list of strings in a TextField
    bus_routes = models.TextField(blank=True)

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.available_seats:
            self.available_seats = self.total_seats
        super().save(*args, **kwargs)

class Booking(models.Model):
    bus = models.ForeignKey(Bus, related_name='bookings', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    seats = models.IntegerField()

    booking_date = models.DateTimeField(default=now)  # Add booking date
    payment_method = models.CharField(max_length=50, blank=True)  # Add payment method
    pickup_location = models.CharField(max_length=255, blank=True)  # Add pickup location
    pickup_time = models.DateTimeField(blank=True)  # Add pickup time
    expected_journey_duration = models.DurationField(blank=True)  # Add journey duration
    destination = models.CharField(max_length=255, blank=True)  # Add destination
    setoff_time = models.DateTimeField(blank=True)  # Add setoff time
    expected_arrival_time = models.DateTimeField(blank=True)  # Add expected arrival time

    def __str__(self):
        return f"Booking by {self.name} for {self.bus.name}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
