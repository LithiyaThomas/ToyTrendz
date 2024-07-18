from django.urls import path
from . import views

app_name = 'category'

urlpatterns = [
    path('category_list/', views.category_list, name='category_list'),
    path('category_create/', views.category_create, name='category_create'),
    path('<int:pk>/category_update/', views.category_update, name='category_update'),
    path('<int:pk>/category_delete/', views.category_delete, name='category_delete'),
    path('<int:pk>/category_restore/', views.category_restore, name='category_restore'),
]
