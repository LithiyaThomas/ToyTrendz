from django.db import models
from django.conf import settings
from PIL import Image
from brand.models import Brand
from category.models import Category


# Product Model
class Product(models.Model):
    product_name = models.CharField(max_length=100, null=False)
    product_description = models.TextField(max_length=5000, null=False)
    product_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    product_brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    offer_price = models.DecimalField(max_digits=8, decimal_places=2)
    thumbnail = models.ImageField(upload_to="thumbnail_images", null=True, blank=True)
    total_reviews = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def percentage_discount(self):
        if self.price and self.offer_price:
            return int(((self.price - self.offer_price) / self.price) * 100)
        return 0

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)
        if self.thumbnail:
            img = Image.open(self.thumbnail.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.thumbnail.path)

    def __str__(self):
        return f"{self.product_brand.name}-{self.product_name}"


# Product Variant Model
class ProductVariant(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    colour_name = models.CharField(max_length=100, null=False)
    variant_stock = models.PositiveIntegerField(default=0)
    variant_status = models.BooleanField(default=True)  # Optional, if you need an active status
    colour_code = models.CharField(max_length=7, null=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.colour_name}"


# Product Variant Image Model
class ProductVariantImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product_variant_images", default='path_to_default_image.jpg')

    def __str__(self):
        return f"Image for {self.variant.product.product_name} - {self.variant.colour_name}"



#Product Rating
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')))
    review = models.TextField(blank=True)  # Add this line

    def __str__(self):
        return f'{self.product.product_name} - {self.rating}'

