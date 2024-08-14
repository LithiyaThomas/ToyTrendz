from django.shortcuts import render, get_object_or_404 ,redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
from product.models import Product, ProductVariant
from coupon.models import Coupon
from django.views.decorators.http import require_POST
import json


# Create your views here.


@login_required
@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        try:

            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            product_id = data.get("product")
            variant_id = data.get("variant")
            quantity = int(data.get("quantity", 1))

            if not product_id or not variant_id:
                return JsonResponse({"error": "Product and Variant IDs are required"}, status=400)

            user = request.user
            product = get_object_or_404(Product, id=product_id)
            variant = get_object_or_404(ProductVariant, id=variant_id)

            if quantity > variant.variant_stock:
                return JsonResponse({"error": "Not enough stock available"}, status=400)

            with transaction.atomic():
                cart, _ = Cart.objects.get_or_create(user=user)

                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    defaults={"quantity": quantity},
                )

                if not created:
                    if cart_item.quantity + quantity > variant.variant_stock:
                        return JsonResponse({"error": "Not enough stock available"}, status=400)
                    cart_item.quantity += quantity
                    cart_item.save()

                total_price = cart.get_total_price()
                cart.discount_amount, cart.discounted_price = apply_coupon(cart, total_price)
                cart.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Variant added to cart',
                    'total_price': float(total_price),
                    'discount_amount': float(cart.discount_amount),
                    'discounted_price': float(cart.discounted_price)
                })

        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except ProductVariant.DoesNotExist:
            return JsonResponse({"error": "Variant not found"}, status=404)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


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
        subtotal = 0
        for item in cart_items:
            item.total_price = item.quantity * item.variant.product.offer_price
            subtotal += item.total_price


        discount_amount, total = apply_coupon(cart, subtotal)

    except Cart.DoesNotExist:

        cart = Cart.objects.create(user=request.user)
        cart_items = []
        subtotal = 0
        discount_amount = 0
        total = 0


    is_cart_empty = len(cart_items) == 0

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'is_cart_empty': is_cart_empty,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total': total
    }
    return render(request, 'cart/view_cart.html', context)


@login_required
@csrf_exempt
def remove_cart_item(request, item_id):
    if request.method == "POST":
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart = cart_item.cart
            cart_item.delete()

            total_price = cart.get_total_price()
            cart.discount_amount, cart.discounted_price = apply_coupon(cart, total_price)
            cart.save()


            cart_items = CartItem.objects.filter(cart=cart)
            total_items = cart_items.count()

            return JsonResponse({
                "success": True,
                "cart_total": float(cart.discounted_price),
                "total_items": total_items,
                "message": "Item removed successfully"
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

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


        item_price = cart_item.variant.product.offer_price
        item_total = item_price * quantity


        user_cart_items = CartItem.objects.filter(cart__user=request.user)


        cart_total = sum(item.variant.product.offer_price * item.quantity for item in user_cart_items)
        total_items = user_cart_items.count()

        return JsonResponse({
            'success': True,
            'item_price': float(item_price),
            'item_total': float(item_total),
            'cart_total': float(cart_total),
            'total_items': total_items
        })

    return JsonResponse({'success': False, 'message': 'Invalid quantity'}, status=400)