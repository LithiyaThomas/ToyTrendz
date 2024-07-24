from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import  AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Address
import re

User = get_user_model()
class RegisterForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'id': 'join_confirm_password',
            'required': True
        })
    )

    class Meta:
        model = User
        fields = ['full_name', 'username', 'email', 'phone', 'password']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Full Name',
                'id': 'join_full_name',
                'required': True
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'Username',
                'id': 'join_username',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Email Address',
                'id': 'join_email_address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '123-456-7890',
                'id': 'phone',
                'required': True
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Password',
                'id': 'join_password',
                'required': True
            }),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '_' in username:
            raise ValidationError('Username should not contain underscores.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValidationError('Enter a valid email address.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r"^\+?1?\d{9,15}$", phone):
            raise ValidationError('Enter a valid phone number.')
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not re.search(r"[A-Z]", password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not re.search(r"[a-z]", password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not re.search(r"[0-9]", password):
            raise ValidationError('Password must contain at least one digit.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError('Password must contain at least one special character.')
        return password

    def clean_confirm_password(self):
        confirm_password = self.cleaned_data.get('confirm_password')
        password = self.cleaned_data.get('password')
        if confirm_password != password:
            raise ValidationError('Passwords do not match.')
        return confirm_password

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if not full_name.strip():
            raise ValidationError('Full name cannot be empty or consist only of whitespace.')
        return full_name

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password and Confirm Password do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        max_length=254,
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True, 'placeholder': 'Email'})
    )

    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone_number', 'address_line_1',
            'address_line_2', 'city', 'state',
            'postal_code', 'country', 'is_default'
        ]