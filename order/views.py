from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem, Payment, Address
from django.db import transaction
from .models import Address
from cart.models import Cart, CartItem
from django.urls import reverse


@login_required
def list_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Prefetch related items to avoid N+1 queries
    orders = orders.prefetch_related(
        'items',
        'items__product',
        'items__variant'
    )
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')

    try:
        paginated_orders = paginator.page(page)
    except PageNotAnInteger:
        paginated_orders = paginator.page(1)
    except EmptyPage:
        paginated_orders = paginator.page(paginator.num_pages)

    context = {
        'orders': paginated_orders,
        'order_count': orders.count(),  # Add total order count for reference
    }

    return render(request, 'order/order_list.html', context)


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
        if order.status in ['Pending', 'Confirmed', 'Shipped']:
            with transaction.atomic():
                # Update stock levels for each item in the order
                for item in order.items.all():
                    if item.variant:
                        variant = item.variant
                        variant.variant_stock += item.quantity
                        variant.save()

                # Update the order status
                order.status = 'Cancelled'
                order.save()

                # Handle payment refund if applicable
                if order.payment_method in ['online_payment', 'wallet']:
                    amount = order.total_price
                    Payment.objects.create(
                        order=order,
                        amount_paid=amount,
                        payment_method=order.payment_method,
                        transaction_id=f"REFUND-{order.uuid}"
                    )

                messages.success(request, "Order cancelled successfully.")
            return redirect('order:list_orders')
        else:
            messages.error(request, "Cannot cancel this order.")

    return redirect('order:order_detail', order_uuid=order.uuid)

@login_required
def proceed_to_payment(request):
    addresses = Address.objects.filter(user=request.user)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = None

    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
        for item in cart_items:
            if item.quantity > item.variant.variant_stock:
                messages.error(request, f"Insufficient stock for {item.product.product_name}.")
                return redirect('cart:view_cart')
            if not item.product.is_active or not item.variant.variant_status:
                messages.error(request, f"{item.product.product_name} is no longer available.")
                return redirect('cart:view_cart')
        cart_total = sum(item.get_total_price() for item in cart_items)
    else:
        cart_items = []
        cart_total = 0

    payment_options = ['Credit Card', 'Debit Card', 'PayPal', 'Cash on Delivery']

    return render(request, 'order/proceed_to_payment.html', {
        'addresses': addresses,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'payment_options': payment_options
    })


@login_required
def place_order(request):
    if request.method == "POST":
        address_id = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        if not address_id or not payment_method:
            messages.error(request, "Please select an address and payment method.")
            return redirect('order:checkout')

        try:
            with transaction.atomic():
                address = get_object_or_404(Address, id=address_id, user=request.user)
                cart = Cart.objects.get(user=request.user)
                cart_items = CartItem.objects.filter(cart=cart)

                if not cart_items.exists():
                    messages.error(request, "Your cart is empty.")
                    return redirect('order:checkout')

                for item in cart_items:
                    if item.quantity > item.variant.variant_stock:
                        messages.error(request, f"Insufficient stock for {item.product.product_name}.")
                        return redirect('cart:view_cart')
                    if not item.product.is_active or not item.variant.variant_status:
                        messages.error(request, f"{item.product.product_name} is no longer available.")
                        return redirect('cart:view_cart')

                cart_total = sum(item.get_total_price() for item in cart_items)

                order = Order.objects.create(
                    user=request.user,
                    total_price=cart_total,
                    payment_method=payment_method,
                    address=address
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.product.offer_price
                    )

                    if item.variant:
                        if item.variant.variant_stock < item.quantity:
                            raise ValueError(f"Not enough stock for {item.product.product_name} - {item.variant.colour_name}")
                        item.variant.variant_stock -= item.quantity
                        item.variant.save()

                cart_items.delete()
                cart.delete()

                messages.success(request, "Your order has been placed successfully!")
                return redirect('order:order_success', order_uuid=order.uuid)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('order:checkout')
        except Exception as e:
            messages.error(request, "An error occurred while processing your order. Please try again.")
            return redirect('order:checkout')

    else:
        return redirect('order:checkout')

@login_required
def order_success(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    context = {
        'order': order,
        'order_id': order.id,

    }
    return render(request, 'order/order_success.html', context)


def add_address(request):
    if request.method == 'POST':
        # Extract form data
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        is_default = request.POST.get('is_default') == 'on'

        # Create new address
        new_address = Address(
            user=request.user,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )

        try:
            new_address.save()
            messages.success(request, 'New address added successfully.')
        except Exception as e:
            messages.error(request, f'Error adding new address: {str(e)}')

    # Redirect to cart checkout page
    return redirect(reverse('order:checkout'))


@login_required
@login_required
def order_detail(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)

    # User information
    user = order.user
    address = order.address

    items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'user': user,
        'address': address,
        'items': items,
    }

    return render(request, 'order/order_detail.html', context)
