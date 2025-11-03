from .models import Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from .views import _cart_id  # if your cart_id function is here

def get_cart_data(request):
    total = 0
    quantity = 0
    shipping_cost = 0
    grand_total = 0
    cart_items = []

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        shipping_cost = 200
        grand_total = total + shipping_cost
    except ObjectDoesNotExist:
        pass

    return {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
