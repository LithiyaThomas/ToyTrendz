# user_panel/forms.py
from django import forms

class RatingForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.IntegerField(
        label='Rating',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    review = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))  # Add this line
