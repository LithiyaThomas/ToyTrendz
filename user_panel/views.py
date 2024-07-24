from django.views.generic import ListView, DetailView, View,UpdateView
from django.shortcuts import redirect, get_object_or_404,render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from product.models import Product, Category, Rating, ProductVariant, ProductVariantImage
from .forms import RatingForm
from django.views.generic import TemplateView
from accounts.models import Address
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from .forms import SimpleUserChangeForm,CustomPasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from cart.models import Wishlist
User = get_user_model()


class UserPanelProductListView(ListView):
    model = Product
    template_name = 'userside/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.all().select_related('product_category', 'product_brand') \
            .prefetch_related(
            Prefetch('productvariant_set',
                     queryset=ProductVariant.objects.prefetch_related('productvariantimage_set'))
        )

        query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        sort_by = self.request.GET.getlist('sort_by')  # Change to getlist to handle multiple values

        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query) |
                Q(product_description__icontains=query)
            )

        if category_id:
            queryset = queryset.filter(product_category_id=category_id)

        # Apply sorting based on the selected checkboxes
        if sort_by:
            ordering = []
            if 'popularity' in sort_by:
                ordering.append('-total_reviews')
            if 'price_low_high' in sort_by:
                ordering.append('price')
            if 'price_high_low' in sort_by:
                ordering.append('-price')
            if 'average_ratings' in sort_by:
                ordering.append('-average_rating')
            if 'new_arrivals' in sort_by:
                ordering.append('-created_at')
            if 'a_to_z' in sort_by:
                ordering.append('product_name')
            if 'z_to_a' in sort_by:
                ordering.append('-product_name')

            if ordering:
                queryset = queryset.order_by(*ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['category_id'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.getlist('sort_by')
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'userside/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Fetch ratings for the product
        ratings = Rating.objects.filter(product=product)

        # Calculate average rating if ratings exist
        if ratings.exists():
            average_rating = ratings.aggregate(Avg('rating'))['rating__avg']
            product.average_rating = round(average_rating, 2)
            product.total_reviews = ratings.count()
            product.save()

        # Fetch thumbnail image if available
        context['thumbnail_image'] = product.thumbnail.url if product.thumbnail else None

        # Fetch variant images
        context['variant_images'] = ProductVariantImage.objects.filter(variant__product=product)

        # Fetch product variants
        variants = ProductVariant.objects.filter(product=product)
        context['variants'] = variants

        # Set the selected variant (default to the first one)
        context['selected_variant'] = variants.first()

        # Fetch images for the selected variant
        if context['selected_variant']:
            context['selected_variant_images'] = ProductVariantImage.objects.filter(variant=context['selected_variant'])

        context['ratings'] = ratings
        context['rating_form'] = RatingForm(initial={'product_id': product.id})
        context['rating_range'] = range(1, 6)


        context['related_products'] = Product.objects.filter(product_category=product.product_category).exclude(
            id=product.id)[:4]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = self.object
            rating.user = request.user
            rating.save()

        return self.render_to_response(self.get_context_data(form=form))




class AddRatingView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = RatingForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            rating = form.cleaned_data['rating']
            review = form.cleaned_data['review']
            product = get_object_or_404(Product, pk=product_id)

            Rating.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                review=review
            )

            return redirect('user_panel:product_detail', pk=product_id)
        else:
            return redirect('user_panel:user_products')


class UserProfile(LoginRequiredMixin, TemplateView):
    template_name = 'userside/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        profiles = Address.objects.filter(user=user, is_deleted=False)

        context['user'] = user
        context['profiles'] = profiles
        return context




class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = SimpleUserChangeForm
    template_name = 'userside/edit_profile.html'
    success_url = reverse_lazy('user_panel:user_profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'userside/change_password.html'
    success_url = reverse_lazy('user_panel:user_profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your password was changed successfully.')
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        # Display error messages if any
        for field in form:
            if field.errors:
                messages.error(self.request, field.errors.as_text())
        return response


class AddToWishlistView(LoginRequiredMixin, View):
    login_url = 'accounts:user_login'

    def post(self, request, *args, **kwargs):
        variant_id = self.kwargs.get('variant_id')
        variant = get_object_or_404(ProductVariant, id=variant_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user, variant=variant)

        if created:
            return JsonResponse({'success': True, 'message': 'Product added to wishlist.'})
        else:
            return JsonResponse({'success': False, 'message': 'Product already in wishlist.'})


class RemoveFromWishlistView(LoginRequiredMixin, View):
    login_url = 'accounts:user_login'

    def post(self, request, *args, **kwargs):
        variant_id = self.kwargs.get('variant_id')
        variant = get_object_or_404(ProductVariant, id=variant_id)

        try:
            wishlist_item = Wishlist.objects.get(user=request.user, variant=variant)
            wishlist_item.delete()
            return JsonResponse({'success': True, 'message': 'Product removed from wishlist.'})
        except Wishlist.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found in wishlist.'})


class WishlistListView(LoginRequiredMixin, ListView):
    model = Wishlist
    template_name = 'userside/wish-list.html'
    context_object_name = 'wishlist_items'
    login_url = 'accounts:user_login'

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
