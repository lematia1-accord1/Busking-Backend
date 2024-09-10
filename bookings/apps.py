from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.exceptions import AppRegistryNotReady


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'

    def create_permissions(self, sender, **kwargs):
        try:
            # Import models within the function to avoid circular imports
            from .models import Bus, Merchant, Booking, User, Customer
            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth.models import Permission

            # Get the ContentType for your models
            bus_content_type = ContentType.objects.get_for_model(Bus)
            merchant_content_type = ContentType.objects.get_for_model(Merchant)
            booking_content_type = ContentType.objects.get_for_model(Booking)
            user_content_type = ContentType.objects.get_for_model(User)
            customer_content_type = ContentType.objects.get_for_model(Customer)

            # Create permissions for models
            Permission.objects.get_or_create(
                codename='add_bus',
                defaults={'name': 'Can add bus', 'content_type': bus_content_type}
            )
            Permission.objects.get_or_create(
                codename='change_bus',
                defaults={'name': 'Can change bus', 'content_type': bus_content_type}
            )
            Permission.objects.get_or_create(
                codename='delete_bus',
                defaults={'name': 'Can delete bus', 'content_type': bus_content_type}
            )
            Permission.objects.get_or_create(
                codename='view_bus',
                defaults={'name': 'Can view bus', 'content_type': bus_content_type}
            )
            Permission.objects.get_or_create(
                codename='view_merchant',
                defaults={'name': 'Can view merchant', 'content_type': merchant_content_type}
            )
            Permission.objects.get_or_create(
                codename='view_booking',
                defaults={'name': 'Can view booking', 'content_type': booking_content_type}
            )
            Permission.objects.get_or_create(
                codename='view_user',
                defaults={'name': 'Can view user', 'content_type': user_content_type}
            )
            Permission.objects.get_or_create(
                codename='view_customer',
                defaults={'name': 'Can view customer', 'content_type': customer_content_type}
            )
        except AppRegistryNotReady:
            # Handle the case where the app registry isn't ready
            pass

    def ready(self):
        # Connect the signal to create permissions
        post_migrate.connect(self.create_permissions, sender=self)
