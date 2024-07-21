from django.views.generic import ListView, DetailView, View,UpdateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from product.models import Product, Category, Rating, ProductVariant, ProductVariantImage
from .forms import RatingForm
from django.views.generic import TemplateView
from accounts.models import Address
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserPanelProductListView(ListView):
    model = Product
    template_name = 'userside/product_list.html'
    context_object_name = 'products'
    paginate_by = 12  # Adjust this number as needed

    def get_queryset(self):
        queryset = Product.objects.all().select_related('product_category', 'product_brand') \
            .prefetch_related(
            Prefetch('productvariant_set',
                     queryset=ProductVariant.objects.prefetch_related('productvariantimage_set'))
        )

        query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        sort_by = self.request.GET.get('sort_by')

        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query) |
                Q(product_description__icontains=query)
            )

        if category_id:
            queryset = queryset.filter(product_category_id=category_id)

        if sort_by:
            if sort_by == 'popularity':
                queryset = queryset.order_by('-total_reviews')
            elif sort_by == 'price_low_high':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_high_low':
                queryset = queryset.order_by('-price')
            elif sort_by == 'average_ratings':
                queryset = queryset.order_by('-average_rating')
            elif sort_by == 'new_arrivals':
                queryset = queryset.order_by('-created_at')
            elif sort_by == 'a_to_z':
                queryset = queryset.order_by('product_name')
            elif sort_by == 'z_to_a':
                queryset = queryset.order_by('-product_name')
            # 'featured' and 'color' options removed

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['sort_by'] = self.request.GET.get('sort_by', '')
        context['search_query'] = self.request.GET.get('q', '')  # Add this line

        # Add query parameters to context for maintaining state in pagination
        context['query_params'] = self.request.GET.copy()
        if 'page' in context['query_params']:
            del context['query_params']['page']
        if 'q' in context['query_params']:  # Add this block
            del context['query_params']['q']

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
        context['rating_range'] = range(1, 6)  # For displaying rating stars

        # Add any additional product information
        context['related_products'] = Product.objects.filter(product_category=product.product_category).exclude(
            id=product.id)[:4]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = self.object
            rating.user = request.user  # Assuming you're using user authentication
            rating.save()
            # Redirect or render as needed
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

        profiles = Address.objects.filter(user=user)

        context['user'] = user
        context['profiles'] = profiles
        return context





class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'userside/edit_profile.html'
    success_url = reverse_lazy('user_panel:user_profile')

    def get_object(self):
        return self.request.user

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'userside/change_password.html'
    success_url = reverse_lazy('user_panel:user_profile')