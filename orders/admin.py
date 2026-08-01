from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['book']
    extra = 0
    readonly_fields = ['price']

    def has_add_permission(self, request, obj=None):
        # Позиції замовлення створюються програмно під час checkout,
        # ручне додавання через адмінку тільки заплутувало б дані.
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'status', 'get_total_cost', 'created_at', 'updated_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'user__email', 'stripe_checkout_session_id']
    readonly_fields = [
        'user', 'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'created_at', 'updated_at',
    ]
    inlines = [OrderItemInline]

    @admin.display(description='Сума')
    def get_total_cost(self, obj):
        return obj.get_total_cost()
