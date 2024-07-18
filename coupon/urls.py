from django.urls import path
from . import views

app_name = 'coupon'

urlpatterns = [
    path('', views.list_coupons, name='list_coupons'),
    path('create/', views.create_coupon, name='create_coupon'),
    path('deactivate/', views.deactivate_coupon, name='deactivate_coupon'),
    path('activate/', views.activate_coupon, name='activate_coupon'),
    path('edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
]
