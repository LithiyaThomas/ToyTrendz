from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from .models import (Product, ProductVariant, Category, Brand,  ProductVariantImage)
from .forms import (ProductForm, ProductVariantForm)
from django.shortcuts import get_object_or_404
from django.views.generic.edit import View
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
def is_admin(user):
    return user.is_superuser

# Product ListView
@method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True), name='dispatch')
@method_decorator(login_required, name='dispatch')
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.select_related('product_category', 'product_brand') \
            .prefetch_related('productvariant_set__productvariantimage_set') \
            .all()

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect('admin-login')
        return super().dispatch(request, *args, **kwargs)


# Product CreateView

class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        return context

# Product UpdateView

class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        return context

    def get_queryset(self):
        return Product.objects.select_related('product_category', 'product_brand').all()

# Product DeleteView

class ProductToggleActiveView(View):
    def get(self, request, *args, **kwargs):
        product = Product.objects.get(pk=kwargs['pk'])
        product.is_active = not product.is_active
        product.save()
        return HttpResponseRedirect(reverse('product:product_list'))


class ProductDetailView(DetailView):
    model = Product
    template_name = 'userside/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object



        # Fetch all variants with their images
        variants = ProductVariant.objects.filter(product=product).prefetch_related('productvariantimage_set')
        
        # Prepare variant data for JSON serialization
        variant_data = []
        for variant in variants:
            variant_images = [{'id': img.id, 'image': img.image.url} for img in variant.productvariantimage_set.all()]
            variant_data.append({
                'id': variant.id,
                'colour_code': variant.colour_code,
                'colour_name': variant.colour_name,
                'images': variant_images
            })

        context['variants'] = variants
        context['variant_data_json'] = json.dumps(variant_data, cls=DjangoJSONEncoder)

        # Set the first variant as default selected
        context['selected_variant'] = variants.first()



        return context
    

# Product Variant CreateView

class ProductVariantCreateView(CreateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'product/product_variant_form.html'

    def get_success_url(self):
        return reverse_lazy('product:product_variants', kwargs={'product_id': self.kwargs['product_id']})

    def form_valid(self, form):
        product_id = self.kwargs['product_id']
        colour_name = form.cleaned_data['colour_name']

        # Check if the color already exists for this product
        if ProductVariant.objects.filter(product_id=product_id, colour_name=colour_name).exists():
            messages.error(self.request, f"The color '{colour_name}' already exists for this product.")
            return self.form_invalid(form)

        form.instance.product_id = product_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs.get('product_id')
        product = Product.objects.get(id=product_id)
        context['product'] = product
        return context

# Product Variant UpdateView
class ProductVariantUpdateView(UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'product/product_variant_form.html'

    def get_success_url(self):
        return reverse_lazy('product:product_variants', kwargs={'product_id': self.object.product_id})

# Product Variant DeleteView

class ProductVariantStatusToggleView(View):
    def post(self, request, *args, **kwargs):
        variant = get_object_or_404(ProductVariant, pk=kwargs['pk'])
        variant.is_active = not variant.is_active
        variant.save()
        return JsonResponse({'status': variant.is_active})

# Product Variant ListView
class ProductVariantListView(ListView):
    template_name = 'product/product_variant_list.html'
    context_object_name = 'variants'

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs['product_id']).prefetch_related('productvariantimage_set')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = Product.objects.get(pk=self.kwargs['product_id'])
        return context


class ProductVariantImageCreateView(View):
    template_name = 'product/productvariantimage_form.html'

    def get(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        return render(request, self.template_name, {'variant': variant})

    def post(self, request, pk):
        variant = get_object_or_404(ProductVariant, pk=pk)
        files = request.FILES.getlist('images')
        for file in files:
            ProductVariantImage.objects.create(variant=variant, image=file)
        return redirect(reverse_lazy('product:product_variants', kwargs={'product_id': variant.product.id}))



# Demo View

class DemoView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/crop.html'
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['brands'] = Brand.objects.all()
        return context
