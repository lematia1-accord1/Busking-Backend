""" from django.contrib import admin
from django.db.models import Sum
from .models import Bus, Booking, User, Merchant, Customer
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError


class MerchantAdmin(admin.ModelAdmin):
    list_display = ('bus_company_name', 'user_email', 'user_is_active', 'approved')
    actions = ['approve_merchants']

    @admin.action(description='Approve selected merchants')
    def approve_merchants(self, request, queryset):
        try:
            current_merchant = Merchant.objects.get(user=request.user)
            if current_merchant.is_default:
                queryset.update(approved=True)
                self.message_user(request, "Selected merchants have been approved.")
            else:
                self.message_user(request, "Only the default merchant can approve other merchants.", level='error')
        except Merchant.DoesNotExist:
            self.message_user(request, "You are not a merchant.", level='error')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_is_active(self, obj):
        return obj.user.is_active
    user_is_active.short_description = 'Active Status'

class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'license_plate', 'total_seats', 'available_seats', 'departure_time', 'arrival_time', 'bus_routes')
    search_fields = ('name', 'license_plate')
    list_filter = ('merchant', 'departure_time', 'arrival_time')

    def available_seats(self, obj):
        return obj.available_seats

    available_seats.short_description = 'Available Seats'

    def save_model(self, request, obj, form, change):
        if obj.merchant and not obj.merchant.is_approved:
            raise ValidationError('The merchant must be approved before adding buses.')
        super().save_model(request, obj, form, change)


class BusNameFilter(SimpleListFilter):
    title = _('Bus Name')
    parameter_name = 'bus__name'

    def lookups(self, request, model_admin):
        buses = Bus.objects.all()
        return [(b.name, b.name) for b in buses]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bus__name=self.value())
        return queryset

class BookingAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'name', 'booking_date', 'seats', 'pickup_location', 'destination', 'expected_journey_duration')
    list_filter = (BusNameFilter, 'booking_date', 'destination')
    search_fields = ('name', 'email')

    def bus_name(self, obj):
        return obj.bus.name

    bus_name.short_description = 'Bus Name'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_seats_booked'] = Booking.objects.aggregate(total_seats=Sum('seats'))['total_seats']
        return super().changelist_view(request, extra_context=extra_context)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user',)

# Register models with their respective admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Merchant, MerchantAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Bus, BusAdmin)
 """

from django.contrib import admin
from django.db.models import Sum
from .models import Bus, Booking, User, Merchant, Customer
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError

class MerchantAdmin(admin.ModelAdmin):
    list_display = ('bus_company_name', 'user_email', 'user_is_active', 'approved')
    actions = ['approve_merchants']

    @admin.action(description='Approve selected merchants')
    def approve_merchants(self, request, queryset):
        try:
            current_merchant = Merchant.objects.get(user=request.user)
            if current_merchant.is_default:
                queryset.update(approved=True)
                self.message_user(request, "Selected merchants have been approved.")
            else:
                self.message_user(request, "Only the default merchant can approve other merchants.", level='error')
        except Merchant.DoesNotExist:
            self.message_user(request, "You are not a merchant.", level='error')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_is_active(self, obj):
        return obj.user.is_active
    user_is_active.short_description = 'Active Status'

class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'license_plate', 'total_seats', 'available_seats', 'departure_time', 'arrival_time', 'bus_routes')
    search_fields = ('name', 'license_plate')
    list_filter = ('merchant', 'departure_time', 'arrival_time')

    def available_seats(self, obj):
        return obj.available_seats

    available_seats.short_description = 'Available Seats'

    def save_model(self, request, obj, form, change):
        if obj.merchant and not obj.merchant.approved:
            raise ValidationError('The merchant must be approved before adding buses.')
        super().save_model(request, obj, form, change)

class BusNameFilter(SimpleListFilter):
    title = _('Bus Name')
    parameter_name = 'bus__name'

    def lookups(self, request, model_admin):
        buses = Bus.objects.all()
        return [(b.name, b.name) for b in buses]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bus__name=self.value())
        return queryset

class BookingAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'name', 'booking_date', 'seats', 'pickup_location', 'destination', 'expected_journey_duration')
    list_filter = (BusNameFilter, 'booking_date', 'destination')
    search_fields = ('name', 'email')

    def bus_name(self, obj):
        return obj.bus.name

    bus_name.short_description = 'Bus Name'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_seats_booked'] = Booking.objects.aggregate(total_seats=Sum('seats'))['total_seats']
        return super().changelist_view(request, extra_context=extra_context)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user',)

# Register models with their respective admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Merchant, MerchantAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Bus, BusAdmin)
