import json
import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from books.models import Book

from .cart import Cart
from .emails import send_order_confirmation_email
from .models import Order, OrderItem

logger = logging.getLogger('django')

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(book=book, quantity=quantity)
    messages.success(request, f"«{book.title}» додано до кошика.")
    return redirect(request.POST.get('next') or 'orders:cart_detail')


@require_POST
def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    messages.info(request, f"«{book.title}» видалено з кошика.")
    return redirect('orders:cart_detail')


@require_POST
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    messages.info(request, "Кошик очищено.")
    return redirect('orders:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})


@login_required
def checkout(request):
    cart = Cart(request)

    if len(cart) == 0:
        messages.error(request, "Кошик порожній — немає що оформлювати.")
        return redirect('orders:cart_detail')

    # transaction.atomic гарантує, що Order і всі його OrderItem
    # створяться всі разом або не створяться взагалі. Якщо після
    # цього виклик Stripe API впаде — весь запис відкотиться,
    # і в базі не залишиться "підвислого" незавершеного замовлення.
    try:
        with transaction.atomic():
            order = Order.objects.create(user=request.user)

            line_items = []
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    book=item['book'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item['book'].title},
                        'unit_amount': int(item['price'] * 100),
                    },
                    'quantity': item['quantity'],
                })

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                customer_email=request.user.email or None,
                success_url=request.build_absolute_uri(
                    reverse('orders:checkout_success')
                ) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('orders:checkout_cancel')),
                metadata={'order_id': str(order.id)},
            )

            order.stripe_checkout_session_id = checkout_session.id
            order.save(update_fields=['stripe_checkout_session_id'])
    except stripe.error.StripeError as exc:
        logger.error(f"Stripe error during checkout: {exc}")
        messages.error(request, "Не вдалося створити сесію оплати. Спробуйте ще раз пізніше.")
        return redirect('orders:cart_detail')

    return redirect(checkout_session.url, permanent=False)


@login_required
def checkout_success(request):
    session_id = request.GET.get('session_id')
    order = None

    if session_id:
        order = Order.objects.filter(stripe_checkout_session_id=session_id).first()

        if order and order.status != Order.Status.PAID:
            # Не довіряємо самому факту редіректу на success_url — це може
            # зробити будь-хто вручну. Перевіряємо реальний статус оплати
            # безпосередньо у Stripe.
            try:
                stripe_session = stripe.checkout.Session.retrieve(session_id)
                if stripe_session.payment_status == 'paid':
                    order.status = Order.Status.PAID
                    order.stripe_payment_intent_id = stripe_session.payment_intent
                    order.save(update_fields=['status', 'stripe_payment_intent_id'])
                    send_order_confirmation_email(order)
                    Cart(request).clear()
            except stripe.error.StripeError as exc:
                logger.error(f"Failed to verify Stripe session {session_id}: {exc}")

    return render(request, 'orders/checkout_success.html', {'order': order})


def checkout_cancel(request):
    return render(request, 'orders/checkout_cancel.html')


@csrf_exempt
def stripe_webhook(request):
    """
    Production-правильний спосіб підтвердження оплати: Stripe сам
    сповіщає наш сервер, замість того щоб покладатись лише на те,
    що браузер користувача дійде до success_url.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning(f"Invalid Stripe webhook payload: {exc}")
        return HttpResponseBadRequest()

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order = Order.objects.filter(
            stripe_checkout_session_id=session['id']
        ).first()

        if order and order.status != Order.Status.PAID:
            order.status = Order.Status.PAID
            order.stripe_payment_intent_id = session.get('payment_intent', '')
            order.save(update_fields=['status', 'stripe_payment_intent_id'])
            send_order_confirmation_email(order)

    return HttpResponse(status=200)
