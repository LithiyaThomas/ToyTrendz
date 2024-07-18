from django.urls import path
from . import views

urlpatterns = [
    path('user-login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('user-register/', views.user_register, name='user_register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('', views.home, name='home'),
    path('address/create/', views.create_address, name='create_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/select/', views.select_address, name='select_address'),

]
