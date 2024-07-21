from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin-login'),
    path('user_data/', views.user_data, name='user_data'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('admin-logout/', views.admin_logout, name='admin-logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-orders/', views.order_list, name='admin_order_list'),
    path('admin-orders/<int:pk>/update-status/', views.update_order_status, name='update_order_status'),
    path('admin-orders/<int:pk>/cancel/', views.cancel_order, name='admin_cancel_order'),

]
