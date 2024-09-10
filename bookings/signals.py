from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def assign_user_role(sender, instance, created, **kwargs):
    if created:
        permissions_to_add = []
        
        if instance.is_guest():
            # Assign guest permissions
            permissions_to_add = [
                'can_view_bus',
                'can_view_booking',
            ]
        elif instance.is_registered():
            # Assign registered user permissions
            permissions_to_add = [
                'can_view_bus',
                'can_book_ticket',
                'can_view_booking_history',
                'can_cancel_booking',
                'can_manage_profile',
            ]
        elif instance.is_admin():
            # Assign admin permissions
            permissions_to_add = [perm.codename for perm in Permission.objects.all()]

        # Add permissions to the user
        for perm_codename in permissions_to_add:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                instance.user_permissions.add(permission)
            except Permission.DoesNotExist:
                # Handle the case where permission does not exist
                pass
