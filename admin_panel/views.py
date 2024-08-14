from django.views.decorators.cache import cache_control
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Sum, OuterRef, Subquery, CharField, Value, F
from accounts.models import User, Wallet, WalletTransaction
from order.models import Order, OrderItem, Payment
from .forms import AdminLoginForm, OrderStatusForm
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
from product.models import Product,ProductVariant,ProductVariantImage
from category.models import Category
from brand.models import Brand

# Check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_admin

def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_admin:
                    auth_login(request, user)
                    request.session['is_admin'] = True
                    return redirect('admin-dashboard')
                else:
                    messages.error(request, 'You are not authorized to access this page.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = AdminLoginForm()

    return render(request, 'adminside/admin_login.html', {'form': form})


def filter_sales_data(period):
    today = timezone.localdate()

    if period == 'yearly':
        start_date = today - timedelta(days=365)
    elif period == 'monthly':
        start_date = today - timedelta(days=30)
    elif period == 'weekly':
        start_date = today - timedelta(days=7)
    elif period == 'daily':
        start_date = today
    else:

        start_date = today


    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    print(f"Start date for period '{period}': {start_datetime}")
    print(f"End date for period '{period}': {end_datetime}")

    if period == 'daily':

        sales_data = Order.objects.filter(created_at__date=today).aggregate(total_sales=Sum('total_price'))
        total_sales = sales_data['total_sales'] or 0
        sales_dates = [today.strftime('%Y-%m-%d')]
        sales_totals = [float(total_sales)]
    else:

        sales_data = Order.objects.filter(created_at__date__gte=start_date).values('created_at__date').annotate(total_sales=Sum('total_price')).order_by('created_at__date')
        sales_dates = [data['created_at__date'].strftime('%Y-%m-%d') for data in sales_data]
        sales_totals = [float(data['total_sales']) for data in sales_data]

    print(f"Period: {period}")
    print(f"Sales Dates: {sales_dates}")
    print(f"Sales Totals: {sales_totals}")

    return sales_dates, sales_totals


@login_required(login_url='admin-login')
def admin_dashboard(request):
    period = request.GET.get('period', 'daily')

    sales_dates, sales_totals = filter_sales_data(period)

    total_revenue = sum(sales_totals)

    start_date = timezone.make_aware(datetime.strptime(sales_dates[0], '%Y-%m-%d'))
    end_date = timezone.make_aware(datetime.strptime(sales_dates[-1], '%Y-%m-%d'))
    total_orders = Order.objects.filter(created_at__range=(start_date, end_date)).count()

    total_products = Product.objects.count()

    order_statuses = ['Pending', 'Completed', 'Cancelled']
    order_counts = [
        Order.objects.filter(created_at__range=(start_date, end_date), status=status).count()
        for status in order_statuses
    ]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'sales_dates': sales_dates,
        'sales_totals': sales_totals,
        'order_statuses': order_statuses,
        'order_counts': order_counts,
    }


    return render(request, 'adminside/dashboard.html', context)




def best_selling(request):

    image_subquery = ProductVariantImage.objects.filter(
        variant=OuterRef('pk')
    ).values('image')[:1]


    default_image_url = settings.MEDIA_URL + 'photos/productvariant/default_image.jpg'


    top_products = ProductVariant.objects.select_related('product').annotate(
        total_quantity=Sum('orderitem__quantity'),
        variant_image=Coalesce(
            Subquery(image_subquery, output_field=CharField()),
            Value(default_image_url, output_field=CharField())
        ),
        offer_price=F('product__offer_price')
    ).values(
        'product__product_name',
        'product__product_category__category_name',
        'product__product_brand__name',
        'product__id',
        'id',
        'offer_price',
        'colour_name',
        'variant_image',
        'total_quantity'
    ).order_by('-total_quantity')[:10]


    for product in top_products:
        product['variant_image'] = settings.MEDIA_URL + product['variant_image']


    top_categories = Category.objects.annotate(
        total_quantity=Coalesce(Sum('product__productvariant__orderitem__quantity'), Value(0))
    ).exclude(total_quantity=0).order_by('-total_quantity')[:10]


    for category in top_categories:
        if category.cat_image:
            category.cat_image_url = category.cat_image.url.replace(settings.MEDIA_URL, '')
        else:
            category.cat_image_url = 'photos/categories/default_category_image.jpg'


    top_brands = Brand.objects.annotate(
        total_quantity=Coalesce(Sum('product__productvariant__orderitem__quantity'), Value(0))
    ).exclude(total_quantity=0).order_by('-total_quantity')[:10]


    context = {
        'top_products': top_products,
        'top_categories': top_categories,
        'top_brands': top_brands,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'adminside/best_selling.html', context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='admin-login')
def user_data(request):
    if not request.session.get('is_admin'):
        return redirect('admin-login')

    users = User.objects.filter(is_admin=False)
    return render(request, 'adminside/user_data.html', {'users': users})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='admin-login')
def block_user(request, user_id):
    if not request.session.get('is_admin'):
        return redirect('admin-login')

    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been blocked.')
    return redirect('user_data')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='admin-login')
def unblock_user(request, user_id):
    if not request.session.get('is_admin'):
        return redirect('admin-login')

    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been unblocked.')
    return redirect('user_data')

def admin_logout(request):
    if request.session.get('is_admin'):
        del request.session['is_admin']
        messages.success(request, 'You have been logged out successfully.')
    return redirect('admin-login')

@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'adminside/order_list.html', {'orders': orders})

@user_passes_test(is_admin)
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order, current_status=order.status)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order status updated successfully.')
            return redirect('admin_order_list')
    else:
        form = OrderStatusForm(instance=order, current_status=order.status)

    return render(request, 'adminside/update_order_status.html', {'form': form, 'order': order})

@user_passes_test(is_admin)
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        if order.status in ['Pending', 'Confirmed', 'Shipped']:
            with transaction.atomic():

                for item in order.items.all():
                    if item.variant:
                        variant = item.variant
                        variant.variant_stock += item.quantity
                        variant.save()


                order.status = 'Cancelled'
                order.save()


                if order.payment_method in ['wallet', 'online_payment']:
                    wallet, created = Wallet.objects.get_or_create(user=order.user)

                    WalletTransaction.handle_order_cancellation(
                        wallet=wallet,
                        order_amount=order.total_price,
                        payment_method=order.payment_method,
                        order=order
                    )

                    if order.payment_method == 'online_payment':
                        Payment.objects.create(
                            order=order,
                            amount_paid=order.total_price,
                            payment_method=order.payment_method,
                            transaction_id=f"REFUND-{order.pk}"
                        )

                messages.success(request, "Order cancelled successfully.")
                return redirect('admin_order_list')
        else:
            messages.error(request, "Cannot cancel this order.")

    return render(request, 'adminside/cancel_order.html', {'order': order})


@user_passes_test(is_admin)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'adminside/order_detail.html', {'order': order, 'order_items': order_items})


def sales_report(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)

            orders = Order.objects.filter(created_at__date__range=[start_date, end_date], status="Delivered")
        else:
            orders = Order.objects.filter(status="Delivered")

        order_items = OrderItem.objects.filter(order__in=orders)
        total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0

        product_counts = order_items.values('product__product_name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('product__product_name')

        # Include product details with each order
        order_details = orders.prefetch_related('orderitem_set__product').values(
            'created_at', 'uuid', 'user__username', 'total_price', 'payment_method', 'coupon_code'
        ).annotate(
            products=OrderItem.objects.filter(order_id=F('id')).values(
                'product__product_name'
            ).annotate(
                total_quantity=Sum('quantity')
            ).order_by('product__product_name')
        )

        data = {
            'orders': list(order_details),
            'total_sales': float(total_sales),
            'product_counts': list(product_counts),
        }

        return JsonResponse(data)

    # Default view for GET request
    orders = Order.objects.filter(status="Delivered")
    order_items = OrderItem.objects.filter(order__in=orders)
    total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0

    product_counts = order_items.values('product__product_name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('product__product_name')

    context = {
        'orders': orders,
        'total_sales': total_sales,
        'product_counts': product_counts,
    }

    return render(request, 'adminside/salesreport.html', context)
