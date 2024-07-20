# accounts/pipeline.py

from social_core.pipeline.partial import partial
from django.shortcuts import redirect

@partial
def save_user_details(strategy, details, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')
    full_name = details.get('fullname') or details.get('name')  # or any other key that might hold the full name
    username = details.get('username') or email.split('@')[0]  # Fallback to part of email if username is not provided
    phone = strategy.session_get('phone')  # Assuming phone is collected separately

    if not email:
        return redirect('request_email')  # Handle this view in your views.py

    if not phone:
        return redirect('request_phone')  # Handle this view in your views.py

    return {
        'is_new': True,
        'user': strategy.create_user(email=email, username=username, full_name=full_name, phone=phone)
    }
