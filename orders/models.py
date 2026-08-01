from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Очікує оплати'
        PAID = 'paid', 'Оплачено'
        CANCELLED = 'cancelled', 'Скасовано'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} ({self.get_status_display()})"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
    )
    book = models.ForeignKey(
        'books.Book',
        related_name='order_items',
        on_delete=models.PROTECT,
    )
    # Ціна фіксується на момент покупки — щоб зміна ціни книги
    # заднім числом не впливала на вже оформлені замовлення.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"

    def get_cost(self):
        return self.price * self.quantity
