from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem, Payment
from django.db import transaction
from .models import Address
from collections import defaultdict


@login_required
def list_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page = request.GET.get('page')

    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def change_order_status(request, order_uuid, new_status):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)

    if request.method == "POST":
        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            messages.success(request, "Order status updated successfully.")
        else:
            messages.error(request, "Invalid status.")

    return redirect('order_detail', order_uuid=order_uuid)


@login_required
def cancel_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)

    if request.method == "POST":
        if order.status in ['Pending', 'Confirmed']:
            with transaction.atomic():
                order.status = 'Cancelled'
                order.save()

                if order.payment_method in ['online_payment', 'wallet']:
                    amount = order.total_price
                    Payment.objects.create(
                        order=order,
                        amount_paid=amount,
                        payment_method=order.payment_method,
                        transaction_id=f"REFUND-{order.uuid}"
                    )
                messages.success(request, "Order cancelled successfully.")
            return redirect('list_orders')
        else:
            messages.error(request, "Cannot cancel this order.")

    return redirect('order_detail', order_uuid=order.uuid)


@login_required
def proceed_to_payment(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    # Handle the payment process here
    # For example, show the payment form, calculate totals, etc.

    return render(request, 'order/proceed_to_payment.html', {'address': address})
