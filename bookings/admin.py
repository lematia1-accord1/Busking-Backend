from django.contrib import admin
from .models import User, Bus, Merchant, Booking, Customer

# Define custom admin classes for Merchant and Customer
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active')

# Register models with their respective admin classes
admin.site.register(User)  # Register your custom User model
admin.site.register(Bus)
admin.site.register(Merchant, MerchantAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Booking)
