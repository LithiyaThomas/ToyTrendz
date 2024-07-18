from django.shortcuts import render, get_object_or_404, redirect
from .models import Brand

# Create your views here.


# List Brands
def brand_list(request):
    brands = Brand.objects.all()
    return render(request, 'brand/brand_list.html', {'brands': brands})

# Create Brand
def brand_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        brand = Brand(name=name)
        brand.save()
        return redirect('brand:brand_list')
    return render(request, 'brand/brand_form.html')

# Update Brand
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.name = request.POST.get('name')
        brand.save()
        return redirect('brand:brand_list')
    return render(request, 'brand/brand_form.html', {'brand': brand})

# Soft Delete Brand
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.soft_delete()
    return redirect('brand:brand_list')

# Restore Brand
def brand_restore(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.restore()
    return redirect('brand:brand_list')
