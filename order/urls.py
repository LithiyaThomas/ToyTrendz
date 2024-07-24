from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('orders/', views.list_orders, name='list_orders'),
    path('orders/<uuid:order_uuid>/status/<str:new_status>/', views.change_order_status, name='change_order_status'),
    path('orders/<uuid:order_uuid>/cancel/', views.cancel_order, name='cancel_order'),
    path('checkout/', views.proceed_to_payment, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_success/<uuid:order_uuid>/', views.order_success, name='order_success'),
    path('add-address/', views.add_address, name='add_address'),
    path('order/<uuid:order_uuid>/', views.order_detail, name='order_detail'),
    path('return-order/<uuid:order_uuid>/', views.return_order, name='return_order'),
]
