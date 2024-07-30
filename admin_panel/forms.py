# admin_panel/forms.py
from django import forms
from order.models import Order

class AdminLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))



class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop('current_status', None)
        super().__init__(*args, **kwargs)

        all_status_choices = Order.STATUS_CHOICES

        if current_status == 'Cancelled':
            self.fields['status'].choices = [choice for choice in all_status_choices if choice[0] == 'Cancelled']
        else:

            self.fields['status'].choices = all_status_choices

