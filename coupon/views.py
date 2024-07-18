from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Coupon
from .forms import CouponForm  # Import the form

@login_required
def list_coupons(request):
    coupons = Coupon.objects.all().order_by('-id')
    current_time = timezone.now()
    for coupon in coupons:
        if coupon.is_active and coupon.is_expired():
            coupon.is_active = False
            coupon.save()
    return render(request, 'admin_panel/coupon/coupon_list.html', {'coupons': coupons})

@login_required
def create_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon:list_coupons')
    else:
        form = CouponForm()
    return render(request, 'admin_panel/coupon/create_coupon.html', {'form': form})

@login_required
def deactivate_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        coupon = get_object_or_404(Coupon, id=coupon_id)
        if not coupon.is_active:
            return JsonResponse({'message': 'Coupon is already inactive'}, status=400)
        coupon.is_active = False
        coupon.save()
        return JsonResponse({'message': 'Coupon deactivated successfully'})
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@login_required
def activate_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        coupon = get_object_or_404(Coupon, id=coupon_id)
        if coupon.is_active:
            return JsonResponse({'message': 'Coupon is already active'}, status=400)
        coupon.is_active = True
        coupon.save()
        return JsonResponse({'message': 'Coupon activated successfully'})
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@login_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon:list_coupons')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin_panel/coupon/coupon_edit.html', {'form': form})

@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.delete()
        return redirect('coupon:list_coupons')
    return render(request, 'admin_panel/coupon/coupon_confirm_delete.html', {'coupon': coupon})
