from django.db.models import Q, Count
from .models import Book,Category

#Filter
expensive_books = Book.objects.filter(price__gt=30)
books_in_stock = Book.objects.filter(stock__gt=0)
horror_books = Book.objects.filter(category__name='Horror')
#Q-requests
king_books = Book.objects.filter(
    Q(title__icontains='The Shining') | Q(author__icontains='Stephen King')
)
available_expensive_books = Book.objects.filter(
    Q(price__gt=50) & Q(stock__gt=0)
)


#Annotate

categories = Category.objects.annotate(
    books_count=Count('books')
)