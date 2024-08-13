from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductToggleActiveView,
    ProductDetailView, ProductVariantCreateView, ProductVariantUpdateView,
    ProductVariantStatusToggleView, ProductVariantListView, ProductVariantImageCreateView,
    DemoView
)

app_name = 'product'

urlpatterns = [
    # Products URLs
    path('productlist/', ProductListView.as_view(), name='product_list'),
    path('create/', ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/toggle-active/', ProductToggleActiveView.as_view(), name='product_toggle_active'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),

    # Product Variants URLs
    path('<int:product_id>/variants/', ProductVariantListView.as_view(), name='product_variants'),
    path('<int:product_id>/variants/create/', ProductVariantCreateView.as_view(), name='product_variant_create'),
    path('variants/<int:pk>/update/', ProductVariantUpdateView.as_view(), name='edit_variant'),
    path('<int:product_id>/variants/', ProductVariantListView.as_view(), name='product_variants'),
    path('variants/images/<int:pk>/add/', ProductVariantImageCreateView.as_view(), name='add_variant_image'),
    path('variant/<int:pk>/toggle-status/', ProductVariantStatusToggleView.as_view(), name='toggle_variant_status'),


 # Demo View
    path('demo/', DemoView.as_view(), name='demo_view'),


]
