from django.shortcuts import render, get_object_or_404, redirect
from .models import Brand
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
# Create your views here.


# List Brands
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='admin-login')
def brand_list(request):
    if not request.session.get('is_admin'):
        return redirect('admin-login')

    brands = Brand.objects.all()
    return render(request, 'brand/brand_list.html', {'brands': brands})

# Create Brand
@login_required(login_url='admin-login')
def brand_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = Brand(name=name)
        brand.save()
        return redirect('brand:brand_list')
    return render(request, 'brand/brand_form.html')

# Update Brand
@login_required(login_url='admin-login')
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.name = request.POST.get('name')
        brand.save()
        return redirect('brand:brand_list')
    return render(request, 'brand/brand_form.html', {'brand': brand})

# Soft Delete Brand
@login_required(login_url='admin-login')
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.soft_delete()
    return redirect('brand:brand_list')

# Restore Brand
@login_required(login_url='admin-login')
def brand_restore(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.restore()
    return redirect('brand:brand_list')
