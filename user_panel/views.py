from django.views.generic import TemplateView
from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView, View, UpdateView
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg
from product.models import Product, Rating, ProductVariant, ProductVariantImage
from .forms import RatingForm, SimpleUserChangeForm, CustomPasswordChangeForm
from accounts.models import Address
from category.models import Category
from cart.models import Wishlist
from offer.models import CategoryOffer
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from order.models import Order
from . import InvoicePDF

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
        sort_by = self.request.GET.getlist('sort_by')

        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query) |
                Q(product_description__icontains=query)
            )

        if category_id:
            queryset = queryset.filter(product_category_id=category_id)


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


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['category_id'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.getlist('sort_by')
        # Include active offers in context if needed
        context['offers'] = CategoryOffer.objects.filter(
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'userside/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object


        ratings = Rating.objects.filter(product=product)


        if ratings.exists():
            average_rating = ratings.aggregate(Avg('rating'))['rating__avg']
            product.average_rating = round(average_rating, 2)
            product.total_reviews = ratings.count()
            product.save()

        # Fetch thumbnail image if available
        context['thumbnail_image'] = product.thumbnail.url if product.thumbnail else None


        context['variant_images'] = ProductVariantImage.objects.filter(variant__product=product)


        variants = ProductVariant.objects.filter(product=product)
        context['variants'] = variants


        context['selected_variant'] = variants.first()


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
    login_url = 'user_login'

    def post(self, request):
        variant_id = request.POST.get('variant_id')
        if not variant_id:
            return JsonResponse({'success': False, 'message': 'Invalid request'})

        try:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product_variant=variant)

            if created:
                return JsonResponse({'success': True, 'message': 'Product added to wishlist', 'action': 'added'})
            else:
                wishlist_item.delete()
                return JsonResponse({'success': True, 'message': 'Product removed from wishlist', 'action': 'removed'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

class RemoveFromWishlistView(LoginRequiredMixin, View):
    login_url = 'user_login'

    def post(self, request, variant_id):
        try:
            print(f"Trying to remove variant_id: {variant_id}")
            wishlist_item = Wishlist.objects.get(user=request.user, product_variant_id=variant_id)
            wishlist_item.delete()
            return JsonResponse({'success': True, 'message': 'Product removed from wishlist.'})
        except Wishlist.DoesNotExist:
            print(f"Wishlist item not found for variant_id: {variant_id}")
            return JsonResponse({'success': False, 'message': 'Product not found in wishlist.'})

class WishlistListView(LoginRequiredMixin, ListView):
    model = Wishlist
    template_name = 'userside/wishlist.html'
    context_object_name = 'wishlists'
    login_url = 'user_login'

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

@login_required
@require_POST
def toggle_wishlist(request):
    variant_id = request.POST.get('variant_id')
    action = request.POST.get('action')

    if not variant_id or not action:
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    try:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product_variant=variant)

        if action == 'add':
            if created:
                message = 'Product added to wishlist.'
            else:
                message = 'Product already in wishlist.'
        elif action == 'remove':
            wishlist_item.delete()
            message = 'Product removed from wishlist.'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'}, status=400)

        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)




@login_required
def check_wishlist(request):
    variant_id = request.GET.get('variant_id')
    if not variant_id:
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

    try:
        variant = ProductVariant.objects.get(id=variant_id)
        in_wishlist = Wishlist.objects.filter(user=request.user, product_variant=variant).exists()
        return JsonResponse({'success': True, 'in_wishlist': in_wishlist})
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Variant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, uuid=order_id, user=request.user)
    items = order.items.all()

    pdf = InvoicePDF()
    pdf.add_page()
    pdf.chapter_title(f'Invoice for Order {order.uuid}')

    address = order.address
    pdf.chapter_body(
        f'Order Date: {order.created_at.strftime("%Y-%m-%d %H:%M:%S")}\n'
        f'Address: {address.address_line_1}, {address.address_line_2}, {address.city}, {address.state}, {address.postal_code}, {address.country}\n'
        f'Order Status: {order.status}\n'
        f'Return Status: {order.return_status}\n'
        f'Discount Price: ₹{order.total_price:.2f}\n'
        f'Payment Method: {order.payment_method}'
    )

    pdf.add_order_items(items)

    # Store PDF content in a BytesIO stream
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    # Set response headers
    response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.uuid}.pdf"'
    return response