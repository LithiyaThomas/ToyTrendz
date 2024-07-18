from django.db import models

class BrandManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'brand'
        verbose_name_plural = 'brands'
        ordering = ['-id']

    def soft_delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def permanent_delete(self):
        super(Brand, self).delete()

    objects = models.Manager()
    available_objects = BrandManager()

    def __str__(self):
        return self.name
