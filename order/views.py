from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Order, OrderItem, Payment,OrderAddress
from django.db import transaction
from cart.models import Cart, CartItem
from django.http import HttpResponse
from accounts.models import Address
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from accounts.models import  Wallet, WalletTransaction
import razorpay
from django.conf import settings
from django.urls import reverse
from coupon.models import Coupon
from django.db.models import Sum
import logging
from decimal import Decimal
from django.utils import timezone
from django.db.models import F


@login_required
def list_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    orders = orders.prefetch_related(
        'items',
        'items__product',
        'items__variant'
    )

    order_subtotals = {}
    for order in orders:
        subtotal = sum(item.product.offer_price * item.quantity for item in order.items.all())
        order_subtotals[order.id] = {
            'subtotal': subtotal,
            'total_with_discount': order.total_price,
            'coupon_discount': order.coupon_discount
        }

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
        'order_count': orders.count(),
        'order_subtotals': order_subtotals,
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
def return_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)
    if request.method == "POST":
        if order.status == 'Delivered' and order.return_status == 'Not Requested':
            with transaction.atomic():
                order.return_status = 'Requested'
                order.save()

                messages.success(request, "Return request submitted successfully.")
        else:
            messages.error(request, "This order cannot be returned.")
    return redirect('order:order_detail', order_uuid=order.uuid)




@login_required
def process_return(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)

    if request.method == "POST":
        action = request.POST.get('action')

        if order.return_status == 'Requested':
            with transaction.atomic():
                try:
                    if action == 'approve':

                        order.return_status = 'Approved'
                        wallet = get_object_or_404(Wallet, user=order.user)


                        WalletTransaction.handle_order_cancellation(
                            wallet=wallet,
                            order_amount=order.total_price,
                            payment_method=order.payment_method,
                            order=order
                        )

                        # Update stock for each item in the order
                        for item in order.items.all():
                            product_variant = item.variant
                            product_variant.variant_stock += item.quantity
                            product_variant.save()


                        order.save()
                        messages.success(request, "Return approved and refund processed.")

                    elif action == 'reject':

                        order.return_status = 'Rejected'
                        order.save()
                        messages.success(request, "Return request rejected.")

                    else:
                        messages.error(request, "Invalid action.")

                except Exception as e:
                    messages.error(request, f"An error occurred: {str(e)}")

        else:
            messages.error(request, "Invalid return status for processing.")

    else:
        messages.error(request, "Invalid request method.")

    return redirect(reverse('admin_order_list'))


@login_required
def cancel_order(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)

    if request.method == "POST":
        if order.status in ['Pending', 'Confirmed', 'Shipped']:
            with transaction.atomic():
                # Update variant stock
                for item in order.items.all():
                    if item.variant:
                        variant = item.variant
                        variant.variant_stock += item.quantity
                        variant.save()

                # Cancel the order
                order.status = 'Cancelled'
                order.save()

                # Handle refunds
                if order.payment_method in ['wallet', 'online_payment']:
                    wallet, created = Wallet.objects.get_or_create(user=request.user)

                    WalletTransaction.handle_order_cancellation(
                        wallet=wallet,
                        order_amount=order.total_price,
                        payment_method=order.payment_method,
                        order=order
                    )

                    if order.payment_method == 'online_payment':
                        # Record the refund
                        Payment.objects.create(
                            order=order,
                            amount_paid=order.total_price,
                            payment_method=order.payment_method,
                            transaction_id=f"REFUND-{order.uuid}"
                        )

                messages.success(request, "Order cancelled successfully.")
                return redirect('order:list_orders')  # Redirect to a list of orders
        else:
            messages.error(request, "Cannot cancel this order.")
            return redirect('order:order_detail', order_uuid=order.uuid)  # Redirect to the order detail page

    # If not POST request, redirect to the order detail page
    return redirect('order:order_detail', order_uuid=order.uuid)

@login_required
def proceed_to_payment(request):

    addresses = Address.objects.filter(user=request.user, is_deleted=False)

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


    payment_options = ['wallet', 'online_payment', 'Cash on Delivery']

    available_coupons = Coupon.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        expiry_date__gt=timezone.now(),
        usage_count__lt=F('overall_usage_limit')
    ).values('code', 'offer_percentage', 'start_date', 'expiry_date')

    return render(request, 'order/proceed_to_payment.html', {
        'addresses': addresses,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'payment_options': payment_options,
        'coupons': available_coupons,
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


                order_address = OrderAddress.objects.create(
                    user=request.user,
                    full_name=address.full_name,
                    phone_number=address.phone_number,
                    address_line_1=address.address_line_1,
                    address_line_2=address.address_line_2,
                    city=address.city,
                    state=address.state,
                    postal_code=address.postal_code,
                    country=address.country
                )

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


                cart_total = request.session.get('cart_total', get_cart_total(request.user))


                coupon_discount = request.session.get('coupon_discount', 0)


                order = Order.objects.create(
                    user=request.user,
                    total_price=cart_total,
                    coupon_discount=Decimal(request.session.get('coupon_discount', '0')),
                    payment_method=payment_method,
                    address=order_address,
                    status='Pending',
                    payment_status='Pending'
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        variant=item.variant,
                        quantity=item.quantity,
                        price=item.product.price,

                    )

                if 'cart_total' in request.session:
                    del request.session['cart_total']
                if 'coupon_discount' in request.session:
                    del request.session['coupon_discount']

                if payment_method == 'online_payment':
                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    razorpay_order = client.order.create({
                        'amount': int(cart_total * 100),
                        'currency': 'INR',
                        'payment_capture': '1'
                    })
                    order.razorpay_order_id = razorpay_order['id']
                    order.save()

                    return render(request, 'order/razorpay_payment.html', {
                        'order': order,
                        'razorpay_order_id': razorpay_order['id'],
                        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                        'callback_url': request.build_absolute_uri(reverse('order:razorpay_callback'))
                    })

                elif payment_method == 'wallet':

                    wallet = get_object_or_404(Wallet, user=request.user)
                    if wallet.balance >= cart_total:
                        wallet.balance -= cart_total
                        wallet.save()

                        WalletTransaction.objects.create(
                            wallet=wallet,
                            amount=cart_total,
                            transaction_type='Debit',
                            description='Payment for order',
                            payment_method=payment_method,
                            order=order
                        )

                        order.payment_status = 'Completed'
                        order.status = 'Confirmed'
                        order.save()

                        # Clear the cart and cart items after successful payment
                        cart_items.delete()
                        cart.delete()

                        messages.success(request, "Payment successful and order confirmed!")
                        return redirect('order:order_success', order_uuid=order.uuid)
                    else:
                        messages.error(request, "Insufficient wallet balance.")
                        order.delete()
                        return redirect('order:checkout')

                else:  # Cash on Delivery
                    if cart_total > Decimal('1000'):
                        messages.error(request, "Cash on Delivery is not available for orders above Rs 1000.")
                        return redirect('order:checkout')

                    order.status = 'Confirmed'
                    order.save()

                    # Clear the cart and cart items after successful order confirmation
                    cart_items.delete()
                    cart.delete()

                    messages.success(request, "Your order has been placed successfully!")
                    return redirect('order:order_success', order_uuid=order.uuid)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('order:checkout')
        except Exception as e:
            messages.error(request, f"An error occurred while processing your order: {str(e)}")
            return redirect('order:checkout')

    else:
        return redirect('order:checkout')

@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            client.utility.verify_payment_signature(params_dict)

            order.payment_status = 'Completed'
            order.status = 'Confirmed'
            order.save()
            # Clear the cart and cart items after successful order confirmation
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            cart_items.delete()
            cart.delete()

            return redirect('order:order_success', order_uuid=order.uuid)
        except Order.DoesNotExist:
            return redirect('order:order_failure', order_uuid=order.uuid)
        except razorpay.errors.SignatureVerificationError:
            return redirect('order:order_failure', order_uuid=order.uuid)
        except Exception as e:
            # Log the error if needed
            print(f"Error: {str(e)}")
            return redirect('order:order_failure', order_uuid=order.uuid)

    return HttpResponse(status=400)

def order_failure(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)

    context = {
        'order': order,
    }
    return render(request, 'order/order_failure.html', context)


@login_required
def order_success(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    order_items = OrderItem.objects.filter(order=order)


    subtotal = sum(item.product.offer_price * item.quantity for item in order.items.all())


    coupon_discount = order.coupon_discount if order.coupon_discount else 0


    total_price = subtotal - coupon_discount

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'discount': coupon_discount,
        'total_price': total_price,
    }
    return render(request, 'order/order_success.html', context)

def add_address(request):
    if request.method == 'POST':

        full_name=request.POST.get('full_name')
        phone_number=request.POST.get('phone_number')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        is_default = request.POST.get('is_default') == 'on'


        new_address = Address(
            user=request.user,
            full_name=full_name,
            phone_number=phone_number,
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

    return redirect(reverse('order:checkout'))


@login_required
def order_detail(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid, user=request.user)

    user = order.user
    address = order.address
    items = order.items.all()

    subtotal = sum(item.product.offer_price * item.quantity for item in items)
    total_with_discount = order.total_price
    coupon_discount = order.coupon_discount

    context = {
        'order': order,
        'user': user,
        'address': address,
        'items': items,
        'subtotal': subtotal,
        'total_with_discount': total_with_discount,
        'coupon_discount': coupon_discount,
    }

    return render(request, 'order/order_detail.html', context)

@require_POST
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code', '').strip()

    if not coupon_code:
        return JsonResponse({'success': False, 'message': 'Coupon code is required.'})

    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)

        if coupon.is_expired():
            return JsonResponse({'success': False, 'message': 'This coupon has expired.'})

        if coupon.remaining_usage() <= 0:
            return JsonResponse({'success': False, 'message': 'This coupon has reached its usage limit.'})

        if not coupon.can_be_used_by_user(request.user):
            return JsonResponse({'success': False, 'message': 'You have already used this coupon the maximum number of times.'})

        cart_total = get_cart_total(request.user)

        if cart_total < coupon.minimum_order_amount:
            return JsonResponse({'success': False, 'message': f'Order total must be at least ${coupon.minimum_order_amount} to use this coupon.'})

        # if coupon.maximum_order_amount > 0 and cart_total > coupon.maximum_order_amount:
        #     return JsonResponse({'success': False, 'message': f'Order total must not exceed ${coupon.maximum_order_amount} to use this coupon.'})

        # Calculate discount
        discount = Decimal(cart_total) * (coupon.offer_percentage / Decimal('100'))
        if discount <coupon.maximum_order_amount:
            discount = discount
        else:
            discount = coupon.maximum_order_amount
        discount = discount.quantize(Decimal('0.01'))
        new_total = Decimal(cart_total) - discount
        new_total = new_total.quantize(Decimal('0.01'))

        # Store the new total and discount in session
        request.session['cart_total'] = float(new_total)
        request.session['coupon_discount'] = float(discount)

        return JsonResponse({
            'success': True,
            'message': 'Coupon applied successfully!',
            'new_total': float(new_total),
            'discount': float(discount)
        })

    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid coupon code.'})

def get_cart_total(user):
    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        total = sum(item.quantity * item.variant.product.offer_price for item in cart_items)
        return total
    except Cart.DoesNotExist:
        return 0


def get_available_coupons(request):
    available_coupons = Coupon.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        expiry_date__gt=timezone.now(),
        usage_count__lt=F('overall_usage_limit')
    ).values('code', 'offer_percentage')

    return JsonResponse({'coupons': list(available_coupons)})


@require_POST
def remove_coupon(request):
    request.session.pop('cart_total', None)
    request.session.pop('coupon_discount', None)

    cart_total = get_cart_total(request.user)

    return JsonResponse({
        'success': True,
        'message': 'Coupon removed successfully!',
        'new_total': float(cart_total)
    })

@login_required
def my_wallet(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-timestamp')


    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate total credits and debits
    total_credit = transactions.filter(transaction_type='Credit').aggregate(Sum('amount'))['amount__sum'] or 0
    total_debit = transactions.filter(transaction_type='Debit').aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'wallet': wallet,
        'transactions': page_obj,
        'total_credit': total_credit,
        'total_debit': total_debit,
    }
    return render(request, 'userside/wallet.html', context)