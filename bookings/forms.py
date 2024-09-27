from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from .models import Bus, Booking, Payment
from .easypay_mobile_money import EasyPayMobileMoney
from django.conf import settings
from django.contrib.auth import get_user_model

#User = settings.AUTH_USER_MODEL
User = get_user_model()

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# Initialize EasyPayMobileMoney instance
easypay = EasyPayMobileMoney()

class BookingForm(forms.ModelForm):
    """
    Form to handle bus booking creation and validation.
    """
    class Meta:
        model = Booking
        fields = [
            'bus', 'name', 'email', 'phone', 'seats', 
            'pickup_location', 'pickup_time', 
            'expected_journey_duration', 'destination'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Custom validation for the booking form.
        """
        cleaned_data = super().clean()
        bus = cleaned_data.get('bus')
        seats = cleaned_data.get('seats')
        pickup_time = cleaned_data.get('pickup_time')

        if pickup_time and pickup_time < now():
            raise ValidationError("Pickup time cannot be in the past.")

        if bus and seats and seats > bus.available_seats:
            raise ValidationError(f"Cannot book {seats} seats. Only {bus.available_seats} seats are available.")

    def save(self, commit=True):
        """
        Save the booking instance and initiate the payment process.
        """
        booking = super().save(commit=False)

        if commit:
            booking.save()
            self.create_payment(booking)

        return booking

    def create_payment(self, booking):
        """
        Initiates payment through EasyPay for the booking.
        """
        amount = booking.bus.price * booking.seats  

        try:
            # Create a payment via EasyPay
            payment_response = easypay.initiate_transaction(
                phone_number=self.user.profile.phone_number,  
                amount=amount,
                transaction_id=f"BOOKING-{booking.id}",
                description=f"Payment for booking {booking.id}"
            )

            if payment_response.get('status') == 'success':
                # Save the payment if successful
                Payment.objects.create(
                    user=self.user,
                    booking=booking,
                    amount=amount,
                    transaction_id=payment_response.get('transaction_id'), 
                )
            else:
                raise ValidationError(f"Payment failed: {payment_response.get('message')}")

        except Exception as e:
            raise ValidationError(f"Error processing payment: {str(e)}")


class PaymentForm(forms.ModelForm):
    """
    Form to handle payment creation and validation.
    """
    class Meta:
        model = Payment
        fields = ['amount', 'transaction_id', 'refunded']

    def clean(self):
        """
        Ensure the transaction ID is present.
        """
        cleaned_data = super().clean()
        if not cleaned_data.get('transaction_id'):
            raise ValidationError("Transaction ID is required.")
        
    
class BusSearchForm(forms.Form):
    """
    Form to search for buses based on source, destination, and date.
    """
    source = forms.CharField(required=True)
    destination = forms.CharField(required=True)
    date = forms.DateField(widget=forms.SelectDateWidget())


class BusForm(forms.ModelForm):
    """
    Form to handle bus details for creation and updating.
    """
    class Meta:
        model = Bus
        fields = [
            'license_plate', 'name', 'total_seats', 
            'bus_routes', 'merchant', 'departure_time', 
            'arrival_time', 'price'
        ]
