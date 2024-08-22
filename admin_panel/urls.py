from django.urls import path
from . import views

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin-login'),
    path('user_data/', views.user_data, name='user_data'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('admin-logout/', views.admin_logout, name='admin-logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/best-selling/', views.best_selling, name='admin-best-selling'),
    path('admin-orders/', views.order_list, name='admin_order_list'),
    path('<int:pk>/update-order_status/', views.update_order_status, name='update_order_status'),
    path('<int:pk>/cancel/', views.cancel_order, name='admin_cancel_order'),
    path('<int:pk>/detail/', views.order_detail, name='order_detail'),
    path('sales-report/', views.sales_report, name='sales_report'),
    # path('sales-data/', views.sales_data, name='sales-data'),
    path('admin/orders/<uuid:order_uuid>/cancel/', views.process_cancel_request, name='process_cancel_request'),

]
