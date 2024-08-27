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
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from order.models import Order,OrderItem

User = get_user_model()

class UserPanelProductListView(ListView):
    model = Product
    template_name = 'userside/product_list.html'
    context_object_name = 'products'
    paginate_by = 4

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

        # Calculate average rating
        ratings = Rating.objects.filter(product=product)
        if ratings.exists():
            average_rating = ratings.aggregate(Avg('rating'))['rating__avg']
            product.average_rating = round(average_rating, 2)
            product.total_reviews = ratings.count()
            product.save()

        # Fetch thumbnail image if available
        context['thumbnail_image'] = product.thumbnail.url if product.thumbnail else None

        show_out_of_stock = self.request.GET.get('show_out_of_stock', 'false') == 'true'

        # Fetch variants based on stock availability
        variants = ProductVariant.objects.filter(product=product)
        if not show_out_of_stock:
            variants = variants.filter(variant_stock__gt=0)

        context['variants'] = variants
        context['variant_images'] = ProductVariantImage.objects.filter(variant__in=variants)

        # Select the first variant by default
        context['selected_variant'] = variants.first()
        if context['selected_variant']:
            context['selected_variant_images'] = ProductVariantImage.objects.filter(variant=context['selected_variant'])

        # Handle user rating
        user_rating = None
        if self.request.user.is_authenticated:
            user_rating = Rating.objects.filter(product=product, user=self.request.user).first()
        context['user_rating'] = user_rating

        context['ratings'] = ratings
        context['rating_form'] = RatingForm(initial={'product_id': product.id})
        context['rating_range'] = range(1, 6)

        # Fetch related products
        context['related_products'] = Product.objects.filter(product_category=product.product_category).exclude(
            id=product.id)[:4]
        context['show_out_of_stock'] = show_out_of_stock
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
    try:

        order_main = get_object_or_404(Order, uuid=order_id)
        order_sub = OrderItem.objects.filter(order=order_main)


        buffer = BytesIO()

        try:

            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []


            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                name='TitleStyle',
                fontName='Helvetica-Bold',
                fontSize=16,
                spaceAfter=12,
                alignment=1,
                textColor=colors.HexColor('#00796b')
            )
            normal_style = ParagraphStyle(
                name='NormalStyle',
                fontName='Helvetica',
                fontSize=12,
                spaceAfter=6,
                alignment=0,
                textColor=colors.black
            )
            heading_style = ParagraphStyle(
                name='HeadingStyle',
                fontName='Helvetica-Bold',
                fontSize=14,
                spaceAfter=6,
                alignment=0,
                textColor=colors.HexColor('#004d40')
            )


            elements.append(Paragraph("COZY CRIBS", title_style))
            elements.append(Paragraph("Invoice", heading_style))
            elements.append(Spacer(1, 12))


            elements.append(Paragraph(f"Order Number: {order_main.uuid}", normal_style))
            elements.append(Paragraph(f"Order Date: {order_main.created_at.strftime('%Y-%m-%d')}", normal_style))
            elements.append(Paragraph(f"Customer Name: {order_main.address.full_name}", normal_style))
            elements.append(Paragraph(f"Email: {order_main.user.email}", normal_style))
            elements.append(Paragraph(f"Phone: {order_main.address.phone_number}", normal_style))
            elements.append(Paragraph(
                f"Address: {order_main.address.address_line_1}, {order_main.address.address_line_2}, {order_main.address.city}, {order_main.address.state}, {order_main.address.postal_code}, {order_main.address.country}",
                normal_style))
            elements.append(Spacer(1, 12))


            data = [['Product', 'Quantity', 'Unit Price', 'Total Price']]
            for item in order_sub:
                data.append([
                    item.product.product_name,
                    str(item.quantity),
                    f"{item.product.offer_price:.2f}",
                    f"{item.get_subtotal():.2f}"
                ])


            data.append(['', '', 'Subtotal:', f"{order_main.total_price:.2f}"])
            data.append(['', '', 'Discount:', f"{order_main.coupon_discount:.2f}"])
            data.append(['', '', 'Shipping:', 'Free'])
            data.append(['', '', 'Total:', f"{order_main.total_price - order_main.coupon_discount:.2f}"])


            table = Table(data)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004d40')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.grey)
            ])
            table.setStyle(table_style)
            elements.append(table)


            doc.build(elements)
        except Exception as e:
            return HttpResponse(f'Error generating PDF content: {str(e)}', status=500)


        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename=f'invoice_{order_id}.pdf')

    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)