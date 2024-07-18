# from django.contrib import admin
# from .models import Type, Product, ProductVariant, ProductImage, Review
#
#
# class ProductImageInline(admin.TabularInline):
#     model = ProductImage
#     extra = 3
#
#
# @admin.register(Type)
# class TypeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_deleted')
#     list_filter = ('is_deleted',)
#     actions = ['restore_selected', 'soft_delete_selected']
#
#     def restore_selected(self, request, queryset):
#         queryset.update(is_deleted=False)
#
#     restore_selected.short_description = "Restore selected types"
#
#     def soft_delete_selected(self, request, queryset):
#         queryset.update(is_deleted=True)
#
#     soft_delete_selected.short_description = "Soft delete selected types"
#
#
# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('product_name', 'category', 'brand', 'product_type', 'is_deleted', 'featured')
#     list_filter = ('is_deleted', 'featured', 'category', 'brand', 'product_type')
#     search_fields = ('product_name',)
#     inlines = [ProductImageInline]
#     actions = ['restore_selected', 'soft_delete_selected']
#
#     def restore_selected(self, request, queryset):
#         queryset.update(is_deleted=False)
#
#     restore_selected.short_description = "Restore selected product"
#
#     def soft_delete_selected(self, request, queryset):
#         queryset.update(is_deleted=True)
#
#     soft_delete_selected.short_description = "Soft delete selected product"
#
#
# @admin.register(ProductVariant)
# class ProductVariantAdmin(admin.ModelAdmin):
#     list_display = ('name', 'product', 'price', 'stock', 'is_active', 'is_deleted')
#     list_filter = ('is_deleted', 'is_active', 'product')
#     search_fields = ('name',)
#     actions = ['restore_selected', 'soft_delete_selected']
#
#     def restore_selected(self, request, queryset):
#         queryset.update(is_deleted=False)
#
#     restore_selected.short_description = "Restore selected variants"
#
#     def soft_delete_selected(self, request, queryset):
#         queryset.update(is_deleted=True)
#
#     soft_delete_selected.short_description = "Soft delete selected variants"
#
#
# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('user', 'variant', 'rating', 'date_added')
#     list_filter = ('rating', 'date_added')
#
#
