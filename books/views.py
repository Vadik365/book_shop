from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Book
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
class BookCreateView(LoginRequiredMixin, CreateView):
    login_url = 'users:login'
    
class BookUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'users:login'
    
class BookDeleteView(LoginRequiredMixin, DeleteView):
    login_url = 'users:login'

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
    
class BookCreateView(CreateView):
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book_list')
    
class BookUpdateView(UpdateView):
    model = Book
    fields = '__all__'
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('book_list')
    
class BookDeleteView(DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('book_list')