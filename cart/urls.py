from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('view/', views.view_cart, name='view_cart'),
    path('update/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('filter/', views.filter_out_of_stock, name='filter_out_of_stock'),
    path('search/', views.advanced_search, name='advanced_search'),
]
