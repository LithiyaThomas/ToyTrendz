from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductToggleActiveView,
    ProductDetailView, ProductVariantCreateView, ProductVariantUpdateView,
    ProductVariantDeleteView, ProductVariantListView, ProductVariantImageCreateView,
    DemoView
)

app_name = 'product'

urlpatterns = [
    # Products URLs
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/toggle-active/', ProductToggleActiveView.as_view(), name='product_toggle_active'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),

    # Product Variants URLs
    path('products/<int:product_id>/variants/', ProductVariantListView.as_view(), name='product_variants'),
    path('products/<int:product_id>/variants/create/', ProductVariantCreateView.as_view(), name='product_variant_create'),
    path('products/variants/<int:pk>/update/', ProductVariantUpdateView.as_view(), name='edit_variant'),
    path('product/products/<int:product_id>/variants/', ProductVariantListView.as_view(), name='product_variants'),
    path('products/variants/images/<int:pk>/add/', ProductVariantImageCreateView.as_view(), name='add_variant_image'),
    path('products/variants/<int:pk>/delete/', ProductVariantDeleteView.as_view(), name='product_variant_delete'),


 # Demo View
    path('demo/', DemoView.as_view(), name='demo_view'),

    # Add more URLs as needed for your project
]
