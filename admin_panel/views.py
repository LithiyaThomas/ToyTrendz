from django.views.decorators.cache import cache_control
from accounts.models import User
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from .forms import AdminLoginForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from order.models import Order, OrderItem
from .forms import OrderStatusForm
from django.contrib.auth.decorators import user_passes_test


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
@login_required
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


def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'adminside/order_list.html', {'orders': orders})

@user_passes_test(is_admin)
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('admin_order_list')
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'adminside/update_order_status.html', {'form': form, 'order': order})

@user_passes_test(is_admin)
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.status = 'Cancelled'
        order.save()
        return redirect('admin_order_list')
    return render(request, 'adminside/cancel_order.html', {'order': order})
