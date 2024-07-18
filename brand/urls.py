from django.urls import path
from . import views

app_name = 'brand'

urlpatterns = [
    path('brand_list/', views.brand_list, name='brand_list'),
    path('brand_create/', views.brand_create, name='brand_create'),
    path('<int:pk>/brand_update/', views.brand_update, name='brand_update'),
    path('<int:pk>/brand_delete/', views.brand_delete, name='brand_delete'),
    path('<int:pk>/brand_restore/', views.brand_restore, name='brand_restore'),
]
