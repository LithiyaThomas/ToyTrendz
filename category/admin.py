# from django.contrib import admin
# from .models import Category
#
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('category_name', 'is_deleted')
#     list_filter = ('is_deleted',)
#     search_fields = ('category_name',)
#     actions = ['restore_selected', 'soft_delete_selected']
#
#     def restore_selected(self, request, queryset):
#         queryset.update(is_deleted=False)
#     restore_selected.short_description = "Restore selected categories"
#
#     def soft_delete_selected(self, request, queryset):
#         queryset.update(is_deleted=True)
#     soft_delete_selected.short_description = "Soft delete selected categories"
#
