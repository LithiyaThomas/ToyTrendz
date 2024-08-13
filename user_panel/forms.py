# user_panel/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import PasswordChangeForm
User = get_user_model()


class SimpleUserChangeForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        # Make the email field read-only
        self.fields['email'].widget.attrs.update({'readonly': 'readonly'})
        self.fields['email'].help_text = None

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if full_name:
            stripped_name = full_name.strip()
            if not stripped_name:
                raise ValidationError(_('Full name cannot be empty or consist of spaces.'))
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            self.phone_validator(phone)
            # Check if phone number is not all zeros
            if phone.strip('0') == '':
                raise ValidationError(_('Phone number cannot be all zeros.'))
        return phone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username contains underscores
            if '_' in username:
                raise ValidationError(_('Username cannot contain underscores.'))
        return username

    def clean_email(self):
        # Ensure email cannot be changed
        if self.instance and self.instance.pk:
            original_email = User.objects.get(pk=self.instance.pk).email
            current_email = self.cleaned_data.get('email')
            if original_email != current_email:
                raise ValidationError(_('Email address cannot be changed.'))
        return self.cleaned_data.get('email')

class RatingForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.IntegerField(
        label='Rating',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    review = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

class CustomPasswordChangeForm(PasswordChangeForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput,
        label=_("New password"),
        help_text=_("Enter a new password. It must be at least 8 characters long, contain at least one letter and one number.")
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput,
        label=_("Confirm new password"),
        help_text=_("Enter the same password as above, for verification.")
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:

            if len(password) < 8:
                raise ValidationError(_('Password must be at least 8 characters long.'))
            if not any(char.isalpha() for char in password):
                raise ValidationError(_('Password must contain at least one letter.'))
            if not any(char.isdigit() for char in password):
                raise ValidationError(_('Password must contain at least one number.'))
        return password


