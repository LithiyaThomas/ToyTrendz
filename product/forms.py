
from django import forms
from .models import Product, ProductVariant, ProductVariantImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_name',
            'product_description',
            'product_category',
            'product_brand',
            'price',
            'offer_price',
            'thumbnail',
            'is_active'
        ]

        # You can customize the widgets if necessary
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'product_description': forms.Textarea(attrs={'rows': 5}),
        }

        # Optional: Add help_texts or labels if needed
        help_texts = {
            'thumbnail': 'Upload a thumbnail image for the product.',
        }

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['colour_name', 'variant_stock', 'variant_status', 'colour_code']


class ProductVariantImageForm(forms.ModelForm):
    class Meta:
        model = ProductVariantImage
        fields = ['image']