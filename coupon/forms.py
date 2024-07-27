# forms.py
from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'start_date', 'expiry_date',
            'offer_percentage', 'minimum_order_amount',
            'maximum_order_amount', 'overall_usage_limit',
            'limit_per_user'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'offer_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'minimum_order_amount': forms.NumberInput(attrs={'min': 0}),
            'maximum_order_amount': forms.NumberInput(attrs={'min': 0}),
            'overall_usage_limit': forms.NumberInput(attrs={'min': 0}),
            'limit_per_user': forms.NumberInput(attrs={'min': 1}),
        }
