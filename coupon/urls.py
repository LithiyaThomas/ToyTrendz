from django.urls import path
from . import views

app_name = 'coupon'
urlpatterns = [
    path('', views.list_coupons, name='list_coupons'),
    path('generate-code/', views.generate_coupon_code, name='generate_coupon_code'),
    path('create/', views.create_coupon, name='create_coupon'),
    path('toggle-coupon-status/<int:coupon_id>/', views.toggle_coupon_status, name='toggle_coupon_status'),
    path('edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

]