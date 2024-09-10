from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db.models import Sum


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


class Merchant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bus_company_name = models.CharField(max_length=255)
    approved = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.bus_company_name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['is_default'], name='unique_default_merchant', condition=models.Q(is_default=True)),
        ]


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
        # Calculate available seats by subtracting the sum of booked seats from total seats
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
        # Perform merchant approval check before saving
        if self.pk is not None:  # Instance already exists
            if not self.merchant.approved:
                raise ValidationError("The merchant must be approved before adding buses.")
        else:  # New instance
            if self.merchant and not self.merchant.approved:
                raise ValidationError("The merchant must be approved before adding buses.")
        
        super().save(*args, **kwargs)

    class Meta:
        permissions = [
            ("can_view_bus", "Can view bus"),
            ("can_manage_bus", "Can manage bus"),
            ("can_view_booking_statistics", "Can view booking statistics"),
        ]
        verbose_name_plural = "Buses"



class Booking(models.Model):
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

    def clean(self):
        if self.pickup_time and self.pickup_time < now():
            raise ValidationError("Pickup time cannot be in the past.")
        if self.seats > self.bus.available_seats:
            raise ValidationError(f"Cannot book {self.seats} seats. Only {self.bus.available_seats} available.")

    def __str__(self):
        return f"Booking by {self.name} for {self.bus.name}"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
