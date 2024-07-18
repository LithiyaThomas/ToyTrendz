from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.list_orders, name='list_orders'),
    path('orders/<uuid:order_uuid>/status/<str:new_status>/', views.change_order_status, name='change_order_status'),
    path('orders/<uuid:order_uuid>/cancel/', views.cancel_order, name='cancel_order'),
    path('payment/proceed/<int:address_id>/', views.proceed_to_payment, name='proceed_to_payment'),
]
