import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger('django')


def send_order_confirmation_email(order):
    """
    Надсилає лист-підтвердження після успішного створення/оплати замовлення.
    Помилка відправки email не повинна ламати сам процес оформлення замовлення,
    тому виняток тут лише логуємо, а не пробрасуємо далі.
    """
    subject = f"Book Store — підтвердження замовлення #{order.id}"
    context = {'order': order, 'items': order.items.select_related('book')}
    message = render_to_string('orders/emails/order_confirmation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent for order #{order.id}")
    except Exception as exc:
        logger.error(f"Failed to send confirmation email for order #{order.id}: {exc}")
