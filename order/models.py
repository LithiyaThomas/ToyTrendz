from django.db import models
from django.conf import settings
import uuid
from decimal import Decimal
from product.models import Product, ProductVariant

# Define the OrderAddress model first
class OrderAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.full_name}, {self.address_line_1}, {self.city}, {self.country}"

# Define the Order model
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    PAYMENT_CHOICES = (
        ('Razorpay', 'Razorpay'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('wallet', 'Wallet'),
    )

    RETURN_CHOICES = (
        ('Not Requested', 'Not Requested'),
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Completed', 'Completed'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='cash_on_delivery')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    return_status = models.CharField(max_length=50, choices=RETURN_CHOICES, default='Not Requested')
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    address = models.ForeignKey(OrderAddress, on_delete=models.CASCADE)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    def __str__(self):
        return f"Order {self.uuid} - {self.user.username}"

# Define the OrderItem model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


    def get_subtotal(self):
        return Decimal(self.product.offer_price) * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} in Order {self.order.uuid}"



# Define the Payment model
class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order {self.order.uuid}"
