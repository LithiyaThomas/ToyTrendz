from django import forms
from .models import ProductOffer, CategoryOffer, ReferralOffer

class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = ['name', 'discount_percentage', 'start_date', 'end_date', 'product']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['name', 'discount_percentage', 'start_date', 'end_date', 'category']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ReferralOfferForm(forms.ModelForm):
    class Meta:
        model = ReferralOffer
        fields = ['name', 'referrer_reward', 'referee_reward', 'eligibility_conditions', 'expiration_date', 'referrer']
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
