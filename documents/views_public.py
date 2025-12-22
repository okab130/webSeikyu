from django.views.generic import TemplateView, FormView, RedirectView
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db import transaction
from .forms import LoginForm, ClientRegisterForm
from .models import RegistrationRequest, RegistrationRequestContact


class IndexView(RedirectView):
    """トップページ - ログイン画面へリダイレクト"""
    pattern_name = 'documents:login'


class LoginView(AuthLoginView):
    """ログイン画面"""
    template_name = 'documents/public/login.html'
    form_class = LoginForm
    
    def get_success_url(self):
        user = self.request.user
        if user.user_type == 'client':
            return reverse_lazy('documents:client_dashboard')
        elif user.user_type in ['staff', 'admin']:
            return reverse_lazy('documents:staff_dashboard')
        else:
            return reverse_lazy('documents:index')


class LogoutView(AuthLogoutView):
    """ログアウト"""
    next_page = 'documents:login'


class ClientRegisterView(FormView):
    """新規取引先登録画面"""
    template_name = 'documents/public/register.html'
    form_class = ClientRegisterForm
    success_url = reverse_lazy('documents:register_confirm')
    
    @transaction.atomic
    def form_valid(self, form):
        # 新規登録依頼を作成
        registration_request = form.save()
        
        # 担当者情報を登録
        contacts_data = []
        for i in range(1, 4):
            name = form.cleaned_data.get(f'contact{i}_name')
            email = form.cleaned_data.get(f'contact{i}_email')
            password = form.cleaned_data.get(f'contact{i}_password')
            
            if name and email and password:
                contacts_data.append({
                    'order': i,
                    'name': name,
                    'email': email,
                    'password': password
                })
        
        for contact_data in contacts_data:
            RegistrationRequestContact.objects.create(
                request=registration_request,
                contact_name=contact_data['name'],
                contact_email=contact_data['email'],
                contact_password=contact_data['password'],
                contact_order=contact_data['order']
            )
        
        return super().form_valid(form)


class RegisterConfirmView(TemplateView):
    """新規登録完了画面"""
    template_name = 'documents/public/register_confirm.html'
