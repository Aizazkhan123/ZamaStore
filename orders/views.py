from django.shortcuts import render
import uuid
# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage


from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.http import HttpResponse
from carts.models import CartItem
from .models import Order
import datetime



def payments(request, order_number):
    payment_method = 'Cash on Delivery'

    # Get order
    order = Order.objects.get(
        user=request.user,
        is_ordered=False,
        order_number=order_number
    )

    # Create random payment ID
    payment_id = str(uuid.uuid4()).replace('-', '')[:10].upper()

    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        payment_id=payment_id,
        payment_method=payment_method,
        amount_paid=order.order_total,
        status='Pending',
    )

    # Update order
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move cart items into OrderProduct
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True,
        )
        order_product.variations.set(item.variations.all())
        order_product.save()

        # Decrease stock
        product = item.product
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send email
    #mail_subject = 'Thank you for your order!'
    #message = render_to_string('orders/order_recieved_email.html', {
        #'user': request.user,
        #'order': order,
    #})
    #email = EmailMessage(mail_subject, message, to=[request.user.email])
    #email.content_subtype = "html"
    #email.send()

    # ⛔️ Remove HttpResponse (It breaks your redirect)
    # 👉 Redirect to order_complete using Django reverse()
    return redirect('order_complete', order_number=order.order_number, payment_id=payment.payment_id)








def place_order(request, total=0, quantity=0):
    current_user = request.user

    # Check if cart has items
    cart_items = CartItem.objects.filter(user=current_user)
    if cart_items.count() <= 0:
        return redirect('store')

    # Calculate totals
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = 200
    grand_total = total + tax

    if request.method == 'POST':
        # Get form data directly from POST
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        country = request.POST.get('country')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        order_note = request.POST.get('order_note')

        # Create and save order manually
        order = Order(
            user=current_user,
            first_name=first_name,
            last_name=last_name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            country=country,
            email=email,
            phone=phone,
            order_note=order_note,
            order_total=grand_total,
            tax=tax,
            ip=request.META.get('REMOTE_ADDR'),
        )
        order.save()

        # Generate order number (YYYYMMDD + ID)
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        current_date = datetime.date(yr, mt, dt).strftime("%Y%m%d")
        order_number = current_date + str(order.id)

        # Save again with generated order number
        order.order_number = order_number
        order.save()

        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
        return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')



def order_complete(request, order_number, payment_id):
    current_user = request.user
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)


        subtotal = 0
        for item in ordered_products:
            subtotal += item.product_price * item.quantity

        payment = Payment.objects.get(payment_id=payment_id)

    

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
