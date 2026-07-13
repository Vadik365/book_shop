from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Book
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin


# Create your views here.
class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 5
    
    def get_queryset(self):
        queryset = Book.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset
    
class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    
class BookCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'books.add_book'
    login_url = 'users:login'
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_list')
    
class BookUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    permission_required = 'books.change_book'
    login_url = 'users:login'
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_list')
    
class BookDeleteView(LoginRequiredMixin,PermissionRequiredMixin, DeleteView):
    permission_required = 'books.delete_book'
    login_url = 'users:login'
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('books:book_list')