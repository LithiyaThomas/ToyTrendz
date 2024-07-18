from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
# Create your models here.


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    offer_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage discount offered by the coupon.'
    )
    minimum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Minimum order amount required to use the coupon.'
    )
    maximum_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Maximum order amount required to use the coupon.'
    )
    overall_usage_limit = models.PositiveIntegerField(
        default=0, help_text='Total number of times the coupon can be used.'
    )
    limit_per_user = models.PositiveIntegerField(
        default=1, help_text='Maximum number of times a single user can use the coupon.'
    )
    usage_count = models.PositiveIntegerField(
        default=0, help_text='Total number of times the coupon has been used.'
    )
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        return timezone.now() > self.expiry_date

    def remaining_usage(self):
        return self.overall_usage_limit - self.usage_count

    def increment_usage(self):
        if self.usage_count < self.overall_usage_limit:
            self.usage_count += 1
            self.save()

    def can_be_used_by_user(self, user):
        # Assuming you have a CouponUsage model to track user-specific usage
        from .models import CouponUsage
        user_usage_count = CouponUsage.objects.filter(coupon=self, user=user).count()
        return user_usage_count < self.limit_per_user

    def __str__(self):
        return self.code

    def clean(self):
        # Ensure start_date is less than expiry_date
        if self.start_date >= self.expiry_date:
            raise ValidationError('Start date must be before expiry date.')
        # Ensure limits are logical
        if self.limit_per_user > self.overall_usage_limit:
            raise ValidationError('Limit per user cannot be greater than overall usage limit.')

class CouponUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} used {self.coupon.code} at {self.used_at}"