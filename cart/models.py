from django.db import models
from django.conf import settings
from product.models import Product, ProductVariant

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon_code = models.CharField(max_length=50, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        price = self.product.offer_price if self.product.offer_price else self.product.price
        return self.quantity * price

    def __str__(self):
        return f"{self.product.product_name} - {self.variant.colour_name} - {self.quantity}"
