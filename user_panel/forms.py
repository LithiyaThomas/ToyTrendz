# user_panel/forms.py
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone']  # Add 'phone' if you have this field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class RatingForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.IntegerField(
        label='Rating',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    review = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))




