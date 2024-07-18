from django.shortcuts import render, get_object_or_404 ,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from product.models import Product, ProductVariant
from coupon.models import Coupon
from django.views.decorators.http import require_POST


# Create your views here.


@login_required
@csrf_exempt  # Use csrf_exempt only if you are handling CSRF protection manually
def add_to_cart(request):
    if request.method == "POST":
        try:
            # Retrieve data from POST request
            product_id = request.POST.get("product")
            variant_id = request.POST.get("variant")
            quantity = int(request.POST.get("quantity", 1))  # Default quantity to 1 if not provided

            # Validate variant_id
            if not variant_id:
                return JsonResponse({"error": "Variant ID is required"}, status=400)

            # Retrieve user and product variant objects
            user = request.user
            product = get_object_or_404(Product, id=product_id)
            variant = get_object_or_404(ProductVariant, id=variant_id)

            # Check if requested quantity exceeds available stock
            if quantity > variant.variant_stock:
                return JsonResponse({"error": "Not enough stock available"}, status=400)

            # Process cart operations within a transaction
            with transaction.atomic():
                # Get or create user's cart
                cart, _ = Cart.objects.get_or_create(user=user)

                # Create or update cart item
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    defaults={"quantity": quantity},
                )

                # If the cart item already exists, update the quantity
                if not created:
                    if cart_item.quantity + quantity > variant.variant_stock:
                        return JsonResponse({"error": "Not enough stock available"}, status=400)
                    cart_item.quantity += quantity
                    cart_item.save()

                # Calculate total price and apply coupon if applicable
                total_price = cart.get_total_price()
                cart.discount_amount, cart.discounted_price = apply_coupon(cart, total_price)
                cart.save()

                # Return success response with updated cart details
                return JsonResponse({
                    'success': True,
                    'message': 'Variant added to cart',
                    'total_price': total_price,
                    'discount_amount': cart.discount_amount,
                    'discounted_price': cart.discounted_price
                })

        except Exception as e:
            # Return error response if any exception occurs
            return JsonResponse({"error": str(e)}, status=400)

    # Return invalid request response for non-POST requests
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def apply_coupon(cart, total_price):
    if cart.coupon_code:
        coupon = Coupon.objects.get(code=cart.coupon_code)
        if not (coupon.minimum_order_amount <= total_price <= coupon.maximum_order_amount):
            cart.coupon_code = None
            return 0, total_price
        discount_amount = (total_price * coupon.offer_percentage) / 100
        return discount_amount, total_price - discount_amount
    return 0, total_price


@login_required
def view_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        for item in cart_items:
            item.total_price = item.quantity * item.variant.product.price
    except Cart.DoesNotExist:
        # Create a new cart if it doesn't exist
        cart = Cart.objects.create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

    return render(request, 'cart/view_cart.html', {'cart': cart, 'cart_items': cart_items})




@login_required
@csrf_exempt
def remove_cart_item(request, item_id):
    if request.method == "POST":
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart_item.delete()

            cart = cart_item.cart
            total_price = cart.get_total_price()
            cart.discount_amount, cart.discounted_price = apply_coupon(cart, total_price)
            cart.save()

            return redirect('cart:view_cart')

            # return JsonResponse({
            #     'success': True,
            #     'message': 'Cart item removed',
            #     'total_price': total_price,
            #     'discount_amount': cart.discount_amount,
            #     'discounted_price': cart.discounted_price
            # })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return redirect('cart:view_cart')

@login_required
def filter_out_of_stock(request):
    show_out_of_stock = request.GET.get('show_out_of_stock') == 'true'
    products = Product.objects.all()

    if not show_out_of_stock:
        products = products.filter(variants__variant_stock__gt=0).distinct()

    return render(request, 'product/product_list.html', {'products': products})

@login_required
def advanced_search(request):
    query = request.GET.get('q')
    sort_by = request.GET.get('sort_by', 'name')  # Default sorting by name
    products = Product.objects.filter(name__icontains=query).order_by(sort_by)
    return render(request, 'product/product_list.html', {'products': products})


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import CartItem
import json


@csrf_exempt
@require_POST
def update_quantity(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'User not authenticated'}, status=401)

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    data = json.loads(request.body)
    quantity = data.get('quantity')

    if quantity and 1 <= quantity <= cart_item.variant.variant_stock:
        cart_item.quantity = quantity
        cart_item.save()

        # Calculate item total and cart total
        item_price = cart_item.variant.product.price
        item_total = item_price * quantity

        # Get all cart items for the user
        user_cart_items = CartItem.objects.filter(cart__user=request.user)

        # Calculate cart total and total items
        cart_total = sum(item.variant.product.price * item.quantity for item in user_cart_items)
        total_items = user_cart_items.count()

        return JsonResponse({
            'success': True,
            'item_price': float(item_price),
            'item_total': float(item_total),
            'cart_total': float(cart_total),
            'total_items': total_items
        })

    return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)