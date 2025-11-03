from .models import Cart, CartItem
from .views import _cart_id  # if your cart_id function is here


def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))

            cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_iteam in cart_items:
                cart_count += cart_iteam.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)