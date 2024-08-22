from django.views.decorators.cache import cache_control
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Sum, OuterRef, Subquery, CharField, Value, F,Prefetch
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
from django.http import HttpResponse
import logging
from django.db.models import Q
from django.db.models import Sum, F
import json
from django.core.serializers.json import DjangoJSONEncoder

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

@login_required(login_url='admin-login')
def admin_dashboard(request):
    period = request.GET.get('period', 'daily')

    # Filter sales data based on the selected period
    sales_dates, sales_totals, total_revenue, total_orders, start_datetime, end_datetime = filter_sales_data(period)

    total_products = Product.objects.count()

    # Calculate the count of orders by status
    order_statuses = ['Pending', 'Completed', 'Cancelled']
    order_counts = [
        Order.objects.filter(created_at__range=(start_datetime, end_datetime), status=status).count()
        for status in order_statuses
    ]

    # Calculate monthly earnings (sum of sales in the last 30 days)
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    monthly_earning = Order.objects.filter(created_at__gte=thirty_days_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0

    data = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'monthly_earning': float(monthly_earning),
        'sales_dates': json.dumps(sales_dates, cls=DjangoJSONEncoder),
        'sales_totals': json.dumps(sales_totals, cls=DjangoJSONEncoder),
        'order_statuses': json.dumps(order_statuses, cls=DjangoJSONEncoder),
        'order_counts': json.dumps(order_counts, cls=DjangoJSONEncoder),
        'period': period
    }

    # Handle AJAX requests to dynamically update data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)

    return render(request, 'adminside/dashboard.html', data)

def filter_sales_data(period):
    today = timezone.localdate()

    # Determine the start date based on the period selected
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

    # Convert start and end dates to aware datetimes
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    # Filter orders within the selected date range
    sales_data = Order.objects.filter(created_at__range=(start_datetime, end_datetime))

    # Calculate total revenue and total orders
    total_revenue = sales_data.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = sales_data.count()

    # Handle different time periods for sales data
    if period == 'daily':
        sales_dates = [today.strftime('%Y-%m-%d')]
        sales_totals = [float(total_revenue)]
    else:
        # Aggregate sales by date
        sales_by_date = sales_data.values('created_at__date').annotate(total_sales=Sum('total_price')).order_by('created_at__date')
        sales_dates = [data['created_at__date'].strftime('%Y-%m-%d') for data in sales_by_date]
        sales_totals = [float(data['total_sales']) for data in sales_by_date]

    return sales_dates, sales_totals, total_revenue, total_orders, start_datetime, end_datetime

def best_selling(request):

    image_subquery = ProductVariantImage.objects.filter(
        variant=OuterRef('pk')
    ).values('image')[:1]


    default_image_url = settings.MEDIA_URL + 'photos/productvariant/default_image.jpg'

    top_products = ProductVariant.objects.select_related('product').annotate(
        total_quantity=Coalesce(Sum('orderitem__quantity'), Value(0)),
        variant_image=Coalesce(
            Subquery(image_subquery, output_field=CharField()),
            Value(default_image_url, output_field=CharField())
        ),
        offer_price=F('product__offer_price')
    ).filter(total_quantity__gt=0).values(
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

    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
        orders = orders.filter(created_at__range=[start_date, end_date])

    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # Filter by payment status
    payment_status = request.GET.get('payment_status')
    if payment_status:
        orders = orders.filter(payment_status=payment_status)

    # Filter by customer (username)
    customer = request.GET.get('customer')
    if customer:
        orders = orders.filter(user__username__icontains=customer)

    # Search by order ID
    search = request.GET.get('search')
    if search:
        orders = orders.filter(Q(uuid__icontains=search) | Q(user__username__icontains=search))

    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'adminside/order_list.html', context)

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


                if order.payment_method in ['wallet', 'Razorpay']:
                    wallet, created = Wallet.objects.get_or_create(user=order.user)

                    WalletTransaction.handle_order_cancellation(
                        wallet=wallet,
                        order_amount=order.total_price,
                        payment_method=order.payment_method,
                        order=order
                    )

                    if order.payment_method == 'Razorpay':
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
    report_type = request.GET.get('report_type', 'custom')

    end_date = timezone.now().date()
    start_date = end_date  # Default to today

    if report_type == 'daily':
        start_date = end_date
    elif report_type == 'weekly':
        start_date = end_date - timedelta(days=7)
    elif report_type == 'yearly':
        start_date = end_date.replace(month=1, day=1)
    elif report_type == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return HttpResponse('Invalid date format', status=400)
        else:
            start_date = end_date - timedelta(days=30)

    orders = Order.objects.filter(created_at__date__range=[start_date, end_date], status="Delivered")
    total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0
    total_discount = orders.aggregate(discount=Sum('coupon_discount'))['discount'] or 0
    overall_orders_count = orders.count()

    # Calculating the total amount with discounts applied
    total_after_discount = total_sales - total_discount

    product_counts = OrderItem.objects.filter(order__in=orders).values('product__product_name').annotate(
        total_quantity=Sum('quantity')
    )

    context = {
        'orders': orders,
        'total_sales': total_sales,
        'total_discount': total_discount,
        'total_after_discount': total_after_discount,
        'overall_orders_count': overall_orders_count,
        'product_counts': product_counts,
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
    }

    return render(request, 'adminside/salesreport.html', context)

@user_passes_test(lambda u: u.is_staff)
def process_cancel_request(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)

    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'approve':
            with transaction.atomic():
                # Update variant stock
                for item in order.items.all():
                    if item.variant:
                        variant = item.variant
                        variant.variant_stock += item.quantity
                        variant.save()

                # Cancel the order
                order.status = 'Cancelled'
                order.return_status = 'Approved'
                order.save()

                # Handle refunds
                if order.payment_method in ['wallet', 'Razorpay']:
                    wallet, created = Wallet.objects.get_or_create(user=order.user)

                    WalletTransaction.handle_order_cancellation(
                        wallet=wallet,
                        order_amount=order.total_price,
                        payment_method=order.payment_method,
                        order=order
                    )

                    if order.payment_method == 'Razorpay':
                        # Record the refund
                        Payment.objects.create(
                            order=order,
                            amount_paid=order.total_price,
                            payment_method=order.payment_method,
                            transaction_id=f"REFUND-{order.uuid}"
                        )

                messages.success(request, "Order cancellation approved and refund initiated.")
            return redirect('admin_order_list')  # Redirect to admin order list

        elif action == 'reject':
            order.return_status = 'Rejected'
            order.save()
            messages.error(request, "Order cancellation request rejected.")
            return redirect('admin_order_list')  # Redirect to admin order list

    # If not POST request, redirect to the order detail page
    return redirect('admin_order_list')