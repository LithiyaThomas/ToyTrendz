
from django import forms
from .models import Product, ProductVariant, ProductVariantImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'product_description', 'product_category', 'product_brand', 'price', 'offer_price', 'thumbnail', 'is_active']

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['colour_name', 'variant_stock', 'variant_status', 'colour_code']


class ProductVariantImageForm(forms.ModelForm):
    class Meta:
        model = ProductVariantImage
        fields = ['image']