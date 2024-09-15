from django.contrib import admin
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from .models import Bus, Booking, User, Merchant, Customer, Payment, Route
from .forms import BookingForm
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.http import HttpResponse
import csv
import requests

# Admin for Merchant
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus_company_name', 'user_email', 'user_is_active', 'approved', 'is_default')
    fields = ('user', 'bus_company_name', 'approved', 'is_default')  # Add fields to the form
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


class BusRoutesFilter(admin.SimpleListFilter):
    title = 'bus routes'
    parameter_name = 'bus_routes'

    def lookups(self, request, model_admin):
        routes = set([bus_route for bus in model_admin.model.objects.all() for bus_route in bus.bus_routes.all()])
        return [(route.id, route.name) for route in routes]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bus_routes__id__exact=self.value())
        return queryset

# Admin for Bus
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'license_plate', 'total_seats', 'available_seats', 'departure_time', 'arrival_time', 'bus_routes')
    search_fields = ('name', 'license_plate')
    list_filter = ('merchant', 'departure_time', 'arrival_time')
    date_hierarchy = 'departure_time'

    def save_model(self, request, obj, form, change):
        if obj.merchant and not obj.merchant.approved:
            self.message_user(request, 'The merchant must be approved before adding buses.', level='error')
        else:
            super().save_model(request, obj, form, change)


# Filter for Bus Name in Bookings
class BusNameFilter(SimpleListFilter):
    title = _('Bus Name')
    parameter_name = 'bus__name'

    def lookups(self, request, model_admin):
        buses = Bus.objects.all()
        return [(b.name, b.name) for b in buses] if buses else []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(bus__name=self.value())
        return queryset


# Admin for Booking
class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ('bus_name', 'name', 'booking_date', 'seats', 'pickup_location', 'destination', 'expected_journey_duration', 'is_paid')
    list_filter = ('bus', 'booking_date', 'destination', 'is_paid')
    search_fields = ('name', 'email')
    actions = ['export_to_csv']

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Bus', 'Seats Booked', 'Booking Time'])
        for booking in queryset:
            writer.writerow([booking.user.username, booking.bus.name, booking.seats, booking.booking_date])
        return response

    export_to_csv.short_description = "Export selected bookings to CSV"

    def bus_name(self, obj):
        return obj.bus.name if obj.bus else 'No Bus Assigned'
    bus_name.short_description = 'Bus Name'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_seats_booked'] = Booking.objects.aggregate(total_seats=Sum('seats'))['total_seats']
        return super().changelist_view(request, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('is_paid',)
        return self.readonly_fields


# Admin for User
class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ('username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'date_joined')
    ordering = ('-date_joined',)


# Admin for Customer
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user',)


class PaymentStatusFilter(admin.SimpleListFilter):
    title = _('payment status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pending', _('Pending')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset
    
# Admin for Payment
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'booking', 'amount', 'transaction_id', 'timestamp', 'refunded', 'status')
    search_fields = ('user__username', 'transaction_id')
    list_filter = ('timestamp', 'refunded', "status")
    list_filter = (PaymentStatusFilter, 'currency')
    actions = ['refund_payments']

    def save_model(self, request, obj, form, change):
        if not obj.transaction_id:
            obj.transaction_id = obj.generate_transaction_id()
        super().save_model(request, obj, form, change)

    @admin.action(description="Refund selected payments")
    def refund_payments(self, request, queryset):
        api_key = settings.EASYPAY_MOBILE_MONEY_API_KEY
        api_url = settings.EASYPAY_MOBILE_MONEY_API_URL
        for payment in queryset:
            try:
                url = f"{api_url}/refund"
                headers = {'Authorization': f'Bearer {api_key}'}
                payload = {'transaction_id': payment.transaction_id}
                response = requests.post(url, headers=headers, json=payload)
                response_data = response.json()

                if response_data['status'] == 'success':
                    payment.refunded = True
                    payment.save()
                    self.message_user(request, f"Payment {payment.transaction_id} refunded successfully.")
                else:
                    self.message_user(request, f"Failed to refund payment {payment.transaction_id}.", level='error')
            except Exception as e:
                self.message_user(request, f"Error processing refund: {str(e)}", level='error')

# Register models with their respective admin classes
admin.site.register(Payment, PaymentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Merchant, MerchantAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(Bus, BusAdmin)

# Unregister default User model to use custom
#admin.site.unregister(User)
