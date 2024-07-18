# from django.contrib import admin
# from .models import Brand
#
# @admin.register(Brand)
# class BrandAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_deleted')
#     list_filter = ('is_deleted',)
#     actions = ['restore_selected', 'soft_delete_selected']
#
#     def restore_selected(self, request, queryset):
#         queryset.update(is_deleted=False)
#     restore_selected.short_description = "Restore selected brands"
#
#     def soft_delete_selected(self, request, queryset):
#         queryset.update(is_deleted=True)
#     soft_delete_selected.short_description = "Soft delete selected brands"
#
