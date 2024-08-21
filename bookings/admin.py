from django.contrib import admin
from .models import Bus, Booking, User, Merchant, Customer

# Register your models here.
admin.site.register(Bus)
admin.site.register(Booking)

class MerchantAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')

# Register models with their respective admin classes
admin.site.register(User)  # Register your custom User model
admin.site.register(Merchant)
admin.site.register(Customer)