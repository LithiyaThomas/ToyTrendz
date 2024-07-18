from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code',
            'start_date',
            'expiry_date',
            'offer_percentage',
            'minimum_order_amount',
            'maximum_order_amount',
            'overall_usage_limit',
            'limit_per_user',
            'is_active'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
