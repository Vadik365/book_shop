from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import RegisterForm

# Create your views here.
class RegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('user:login')

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    
class UserLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')