# # accounts/social_auth_pipeline.py
#
# from social_core.exceptions import AuthAlreadyAssociated
# from django.shortcuts import redirect
# from django.urls import reverse
#
# def handle_associated_account(backend, uid, user=None, *args, **kwargs):
#     if user:
#         return None
#
#     try:
#         user = backend.strategy.storage.user.get_user(user_id=uid)
#     except AuthAlreadyAssociated:
#         return redirect(reverse('login') + '?error=associated')
#
#     return None
