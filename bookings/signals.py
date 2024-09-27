from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def assign_user_role(sender, instance, created, **kwargs):
    """
    Signal to assign role-based permissions to a user upon creation.
    """
    if created:
        # Dictionary mapping user roles to their respective permissions
        role_permissions = {
            'guest': ['can_view_bus', 'can_view_booking'],
            'registered': [
                'can_view_bus', 'can_book_ticket', 'can_view_booking_history',
                'can_cancel_booking', 'can_manage_profile'
            ],
            'admin': [perm.codename for perm in Permission.objects.all()] 
        }

        # Determine the user's role and fetch corresponding permissions
        if instance.is_guest():
            permissions_to_add = role_permissions['guest']
        elif instance.is_registered():
            permissions_to_add = role_permissions['registered']
        elif instance.is_admin():
            permissions_to_add = role_permissions['admin']
        else:
            permissions_to_add = []  

        # Assign permissions to the user
        permissions = Permission.objects.filter(codename__in=permissions_to_add)
        if permissions.exists():
            instance.user_permissions.add(*permissions)

        # Optional: Log or handle the case where permissions could not be found
        missing_permissions = set(permissions_to_add) - set(permissions.values_list('codename', flat=True))
        if missing_permissions:
            # For debugging or logging purposes
            print(f"Warning: Missing permissions: {', '.join(missing_permissions)}")
