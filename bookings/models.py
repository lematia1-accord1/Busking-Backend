from django.db import models;
from django.contrib.auth.models import AbstractUser;
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
    name = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name



class Booking(models.Model):
    bus = models.ForeignKey(Bus, related_name='bookings', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    seats = models.IntegerField()

    def __str__(self):
        return f"Booking by {self.name} for {self.bus.name}"
    
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username