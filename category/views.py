from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import Category
from django.utils.text import slugify
# Create your views here.


# List Categories
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def category_list(request):
    if not request.session.get('is_admin'):
        return redirect('admin-login')

    categories = Category.objects.all()
    return render(request, 'category/category_list.html', {'categories': categories})

# Create Category
@login_required(login_url='admin-login')
def category_create(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        cat_image = request.FILES.get('cat_image')

        # Automatically generate slug if not provided
        if not slug:
            slug = slugify(category_name)

        category = Category(category_name=category_name, slug=slug, description=description, cat_image=cat_image)
        category.save()
        return redirect('category:category_list')
    return render(request, 'category/category_form.html')
# Update Category
@login_required(login_url='admin-login')
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.category_name = request.POST.get('category_name')
        category.slug = request.POST.get('slug')
        category.description = request.POST.get('description')
        if request.FILES.get('cat_image'):
            category.cat_image = request.FILES.get('cat_image')
        category.save()
        return redirect('category:category_list')
    return render(request, 'category/category_form.html', {'category': category})

@login_required(login_url='admin-login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.soft_delete()
    return redirect('category:category_list')

@login_required(login_url='admin-login')
def category_restore(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.restore()
    return redirect('category:category_list')
