from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Coupon
from .forms import CouponForm
import random
import string
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST

@login_required
def list_coupons(request):
    coupons = Coupon.objects.all().order_by('-id')
    current_time = timezone.now()
    for coupon in coupons:
        if coupon.is_active and coupon.is_expired():
            coupon.is_active = False
            coupon.save()
    return render(request, 'coupon/coupon_list.html', {'coupons': coupons})

def generate_coupon_code(request):
    if request.method == 'GET':
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return JsonResponse({'code': code})

def create_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            if request.is_ajax():
                redirect_url = reverse('coupon:list_coupons')  # Generate the URL for redirection
                return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
            return redirect('coupon:list_coupons')
        if request.is_ajax():
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = CouponForm()
    return render(request, 'coupon/create_coupon.html', {'form': form})


@login_required
def toggle_coupon_status(request, coupon_id):
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        action = request.POST.get('action')

        if action == 'activate':
            if coupon.is_active:
                messages.error(request, 'Coupon is already active.')
            else:
                coupon.is_active = True
                coupon.save()
                messages.success(request, 'Coupon activated successfully.')

        elif action == 'deactivate':
            if not coupon.is_active:
                messages.error(request, 'Coupon is already inactive.')
            else:
                coupon.is_active = False
                coupon.save()
                messages.success(request, 'Coupon deactivated successfully.')

        else:
            return HttpResponseBadRequest('Invalid action.')

        return redirect('coupon:list_coupons')
    return HttpResponseBadRequest('Invalid request method.')

@login_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        print('hi')
        if form.is_valid():
            print(form.is_valid())
            form.save()
            return redirect('coupon:list_coupons')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'coupon/coupon_edit.html', {'form': form})

@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.delete()
        return redirect('coupon:list_coupons')
    return render(request, 'coupon/coupon_confirm_delete.html', {'coupon': coupon})
