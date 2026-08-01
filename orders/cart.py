from decimal import Decimal

from django.conf import settings

from books.models import Book


class Cart:
    """
    Session-based кошик товарів.
    Дані зберігаються у request.session, тому кошик "переживає"
    окремі запити, але прив'язаний до конкретної сесії браузера.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, book, quantity=1, override_quantity=False):
        """
        Додати книгу в кошик або оновити її кількість.
        override_quantity=True -> виставити кількість напряму (для форми в кошику),
        override_quantity=False -> додати quantity до вже наявної кількості.
        """
        book_id = str(book.id)
        if book_id not in self.cart:
            self.cart[book_id] = {'quantity': 0, 'price': str(book.price)}

        if override_quantity:
            self.cart[book_id]['quantity'] = quantity
        else:
            self.cart[book_id]['quantity'] += quantity

        if self.cart[book_id]['quantity'] <= 0:
            self.remove(book)
        else:
            self.save()

    def remove(self, book):
        """Повністю прибрати книгу з кошика."""
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        """Очистити кошик повністю (викликається після успішної оплати)."""
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        """
        Ітерується по товарах кошика, підвантажуючи об'єкти Book
        одним запитом, і додає порахований total_price для кожної позиції.
        """
        book_ids = self.cart.keys()
        books = Book.objects.filter(id__in=book_ids)
        books_map = {str(book.id): book for book in books}

        for book_id, item in self.cart.items():
            book = books_map.get(book_id)
            if book is None:
                # Книгу могли видалити з каталогу після додавання в кошик
                continue
            item = item.copy()
            item['book'] = book
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Загальна кількість одиниць товару в кошику."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )
