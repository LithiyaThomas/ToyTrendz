from django.views.decorators.cache import cache_control
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from datetime import datetime
from django.db.models import Sum
from accounts.models import User, Wallet, WalletTransaction
from order.models import Order, OrderItem, Payment
from .forms import AdminLoginForm, OrderStatusForm

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

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url='admin-login')
def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('admin-login')
    return render(request, 'adminside/dashboard.html')

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
                # Restore stock
                for item in order.items.all():
                    if item.variant:
                        variant = item.variant
                        variant.variant_stock += item.quantity
                        variant.save()

                # Update order status
                order.status = 'Cancelled'
                order.save()

                # Handle refunds for wallet and online payments
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
                messages.error(request, 'Invalid date format.')
                return redirect('sales_report')

            orders = Order.objects.filter(created_at__date__range=[start_date, end_date], status="Delivered")
            total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0
            return render(request, 'adminside/salesreport.html', {'orders': orders, 'total_sales': total_sales, 'start_date': start_date, 'end_date': end_date})

    orders = Order.objects.filter(status="Delivered")
    total_sales = orders.aggregate(total=Sum('total_price'))['total'] or 0
    return render(request, 'adminside/salesreport.html', {'orders': orders, 'total_sales': total_sales})