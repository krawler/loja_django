from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.views import View
from . import forms
from .models import PerfilUsuario
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

import copy

class BasePerfil(View):
    
    template_name = 'perfil/criar.html'
    
    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        
        self.carrinho = copy.deepcopy(self.request.session.get('carrinho'), {})
        self.perfil = None
        
        if self.request.user.is_authenticated:
            self.perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()
            self.context = {
                'userform': forms.UserForm(
                                data=self.request.POST or None, 
                                usuario=self.request.user,
                                instance=self.request.user,    
                            ),
                'perfilform': forms.PerfilForm(data=self.request.POST or None)
            }
        else:
            self.context = {
                'userform': forms.UserForm(data=self.request.POST or None),
                'perfilform': forms.PerfilForm(data=self.request.POST or None)
            }
            
        self.userform = self.context['userform']
        self.perfilform = self.context['perfilform']
                
        self.renderizar = render(self.request, self.template_name, self.context)
    
    def get(self, *args, **kwargs):        
        return self.renderizar

class Criar(BasePerfil):
    
    def post(self, *args, **kwargs):
        
        if not self.userform.is_valid() or not self.perfilform.is_valid():
            return self.renderizar
        
        username = self.userform.cleaned_data.get('username')
        password = self.userform.cleaned_data.get('password')
        email = self.userform.cleaned_data.get('email')
        first_name = self.userform.cleaned_data.get('first_name')
        last_name = self.userform.cleaned_data.get('last_name')
        
        if self.request.user.is_authenticated:
            usuario = get_object_or_404(User, username=self.request.user.username)
             
            usuario.username = username
            if password:
               usuario.set_password(password)               
            usuario.email = email 
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.save()
            
            if not self.perfil:
                self.perfilform.cleaned_data['usuario'] = usuario
                perfil = PerfilUsuario(**self.perfilform.cleaned_data)
                perfil.save()
            else:
                perfil = self.perfilform.save(commit=False)
                perfil.usuario = usuario
                perfil.save()
        else:
            usuario = self.userform.save(commit=False)
            usuario.set_password(password)
            usuario.save()
            
            perfil = self.perfilform.save(commit=False)
            perfil.usuario = usuario
            perfil.save()
        
        if password:
            authentica = authenticate(
                self.request,
                username=username,
                password=password
            )
            if authentica:
                login(self.request, user=usuario)
        
        self.request.session['carrinho'] = self.carrinho
        self.request.session.save()       
        
        return self.renderizar

class Atualizar(View):
    pass

class Login(View):
    def post(self, *args, **kwargs):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        
        print('usuario logado')
        
        if not username or not password:
            messages.error(
                self.request,
                'Usuário ou senha inválidos'
            )
            return redirect('perfil:criar')
        
        usuario = authenticate(self.request, username=username, password=password)
        
        if not usuario:
            messages.error(
                self.request,
                "Usuário ou senha inválidos"
            )
            return redirect('perfil:criar')
        
        login(self.request, user=usuario)
        
        print(self.request.user)
        
        if self.request.session.get('carrinho'):
            return redirect('produto:carrinho')             
            
        return redirect('produto:lista')        


class Logout(View):
    def get(self, *args, **kwargs):
        carrinho = copy.deepcopy(self.request.session.get('carrinho'))
        logout(self.request)
        self.request.session['carrinho'] = carrinho
        self.request.session.save()
        return redirect('produto:lista')