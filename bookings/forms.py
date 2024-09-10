from django import forms
from django.core.exceptions import ValidationError
from .models import Bus

class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        merchant = cleaned_data.get('merchant')

        if merchant and not merchant.is_approved:
            raise ValidationError('The merchant must be approved before adding buses.')
