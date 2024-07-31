# apps.py
from django.apps import AppConfig


from django.contrib.contenttypes.models import ContentType
# from .models import Bus, Merchant, Booking, User, Customer

from django.db.models.signals import post_migrate


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def create_permissions(self, sender, **kwargs):
        # Import models within the function to avoid circular imports
        from .models import Bus, Merchant, Booking, User, Customer
        from django.contrib.auth.models import Permission

        # Get the ContentType for your models (use self for model reference)
        bus_content_type = ContentType.objects.get_for_model(
            self.get_model('Bus'))
        merchant_content_type = ContentType.objects.get_for_model(
            self.get_model('Merchant'))
        booking_content_type = ContentType.objects.get_for_model(
            self.get_model('Booking'))
        user_content_type = ContentType.objects.get_for_model(
            self.get_model('User'))
        customer_content_type = ContentType.objects.get_for_model(
            self.get_model('Customer'))

        # Create permissions for merchants (using get_or_create)
        Permission.objects.get_or_create(
            codename='add_bus',
            name='Can add bus',
            content_type=bus_content_type
        )
        Permission.objects.get_or_create(
            codename='change_bus',
            name='Can change bus',
            content_type=bus_content_type
        )
        Permission.objects.get_or_create(
            codename='delete_bus',
            name='Can delete bus',
            content_type=bus_content_type
        )
        Permission.objects.get_or_create(
            codename='view_bus',
            name='Can view bus',
            content_type=bus_content_type
        )
        Permission.objects.get_or_create(
            codename='view_merchant',
            name='Can view merchant',
            content_type=merchant_content_type
        )
        Permission.objects.get_or_create(
            codename='view_booking',
            name='Can view booking',
            content_type=booking_content_type
        )
        Permission.objects.get_or_create(
            codename='view_user',
            name='Can view user',
            content_type=user_content_type
        )
        Permission.objects.get_or_create(
            codename='view_customer',
            name='Can view customer',
            content_type=customer_content_type
        )

# Connect the signal


    def ready(self):
        # Connect the signal (use self for method reference)
        post_migrate.connect(self.create_permissions, sender=self)
