from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from PIL import Image

class CategoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['-id']

    def get_url(self):
        return reverse('product_list_by_category', args=[self.slug])

    def soft_delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def permanent_delete(self):
        super(Category, self).delete()

    objects = models.Manager()
    available_objects = CategoryManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)
        if self.cat_image:
            img = Image.open(self.cat_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.cat_image.path)

    def __str__(self):
        return self.category_name
