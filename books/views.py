from django.shortcuts import render
from books.models import Book


# Create your views here.
def main_page(request):
    result = Book.objects.all()
    author = Book.objects.get(pk=1)
    result = Book.objects.filter(author=author)
    return ''