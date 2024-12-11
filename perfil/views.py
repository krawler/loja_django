from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import ListView
from django.views import View
from datetime import datetime
from . import forms
from .models import PerfilUsuario, PasswordResetCode
from produto.models import Produto
from produto.produto_service import ProdutoService
from perfil.templates.email.py_email import PyEmail
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
import copy
import json
import random
import string

class BasePerfil(View):
    
    template_name = 'perfil/criar.html'
    
    def setup(self, *args, **kwargs):
        
        super().setup(*args, **kwargs)
        
        self.carrinho = copy.deepcopy(self.request.session.get('carrinho'), {})
        self.perfil = None

        if self.request.user.is_authenticated:
            self.perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()
            self.usuario = User.objects.filter(username=self.request.user).first()
        
            self.context = {
                'userform': 
                            forms.UserForm(
                                data=self.request.POST or None, 
                                usuario=self.request.user,
                                instance=self.request.user,    
                            ),
                'perfilform': 
                            forms.PerfilForm(
                                data=self.request.POST or None,
                                instance=self.perfil, 
                                perfil=self.perfil),
                'produtos_mais_vendidos' : ProdutoService().get_produtos_mais_vendidos(),
                'pagina_cadastro': True 
            }
        else:
            self.context = {
                'userform': forms.UserForm(data=self.request.POST or None),
                'perfilform': forms.PerfilForm(data=self.request.POST or None),
                'produtos_mais_vendidos' : ProdutoService().get_produtos_mais_vendidos(),
                'pagina_cadastro': True 
            }
            
        self.userform = self.context['userform']
        self.perfilform = self.context['perfilform']
                
        self.renderizar = render(self.request, self.template_name, self.context)
    
    def get(self, *args, **kwargs):        
        return self.renderizar

class Criar(BasePerfil):
    
    def post(self, *args, **kwargs):
        
        if not self.userform.is_valid() or not self.perfilform.is_valid():    
            msg = 'Há erros no formulário, por favor verifique nos campos abaixo'  
            messages.error(self.request, msg)             
            return self.renderizar

        password = self.userform.cleaned_data.get('password')
        email = self.userform.data.get('email')
        nome_completo = self.perfilform.cleaned_data.get('nome_completo')
        nomes = nome_completo.split(' ')
        first_name = nomes[0]
        tamanho_lista = len(nomes)
        last_name = nomes[tamanho_lista - 1]

        username = str(email).split('@')[0]

        if self.request.user.is_authenticated:
            usuario = get_object_or_404(User, username=self.request.user.username)
            
            usuario.username = username
            if password:
                usuario.set_password(password)           
            usuario.email = email 
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.save(force_update=True)
            
            if not self.perfil:
                self.perfilform.cleaned_data['usuario'] = usuario
                perfil = PerfilUsuario(**self.perfilform.cleaned_data)
                perfil.save()
            else:
                perfil = self.perfilform.save(commit=False)
                perfil.usuario = usuario
                perfil.save(force_update=True)
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

        return redirect('perfil:cadastro_concluido')
            

class Cadastro_concluido(View):
    model = PerfilUsuario
    context_object_name = 'perfil'
    template_name = 'perfil/cadastro_concluido.html'
    paginate_by = 3

    def get(self, *args, **kwargs):
        usuario = self.request.user
        perfil = PerfilUsuario.objects.filter(usuario=usuario).get() 
        produtos = Produto.objects.all()[:3:1]
        contexto = {
            'usuario': usuario,
            'perfil' : perfil,
            'produtos': produtos,
            'produtos_mais_vendidos' : ProdutoService().get_produtos_mais_vendidos() 
        }  
        
        return render(self.request, self.template_name, contexto)

class Atualizar(Criar):

    template_name = 'perfil/atualizar.html'
    
    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('perfil:login')
        
        return self.renderizar    

class Login(View):

    def get(self, *args, **kwargs):

        contexto = {
            'area_sem_produtos' : True
        }
        return render(self.request, 'perfil/login.html', contexto)

    def post(self, *args, **kwargs):
        username = self.request.POST.get('username')
        password = self.request.POST.get('password')
        
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
            return redirect('perfil:login')
        
        login(self.request, user=usuario)
        
        if not self.request.session.get('carrinho'):
            self.request.session['carrinho'] = {}
            self.request.session.save()
            
        carrinho_sessao = self.request.session['carrinho']
        carrinho_bd = ProdutoService().getCarrinhoSessao(usuario) 
        if carrinho_bd is not None:
            for item in carrinho_bd:
                carrinho_sessao[item.Variacao.id] = {
                    'variacao_id': item.Variacao.id,
                    'variacao_nome': item.Variacao.nome,
                    'produto_nome': item.Variacao.produto.nome,
                    'imagem': json.dumps(str(item.Variacao.produto.imagem)),
                    'preco_quantitativo': item.preco_quantitativo,
                    'preco_quantitativo_promocional': item.preco_quantitativo_promocional,
                    'quantidade': item.quantidade,
                    'slug': item.slug,
                    'produto_id': item.Variacao.produto.id
                }
                    
        if carrinho_sessao is not None:
            return redirect('produto:carrinho')             
            
        return redirect('produto:lista')        


class Logout(View):

    def get(self, *args, **kwargs):
        
        carrinho = self.request.session.get('carrinho')
        
        logout(self.request)
        self.request.session.save()
        return redirect('produto:lista')

class Password_Reset(View):

    def get(self, *args, **kwargs):
        form = form = PasswordResetForm()        
        return render(self.request, 'perfil/password_reset.html', {'form': form, 'mensagem': ''})
    
    def post(self, *args, **kwargs):
        form = PasswordResetForm(self.request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                code = ''.join(random.choices(string.digits, k=8))
                token = default_token_generator.make_token(user)
                password_reset = PasswordResetCode.objects.create(usuario=user, codigo=code, token=token)
                subject = 'Recuperação de Senha'
                message = render_to_string('email/template_password_reset.html', {'code': code})
                
                py_email = PyEmail(email)
                py_email.set_body(user.perfilusuario.nome_completo, code, self.request)
                py_email.enviar()

                if user is not None:    
                    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
                    self.request.session['uidb64'] = uidb64
                    self.request.session.save()

                return redirect('perfil:code_verification')

            except User.DoesNotExist:
                messages.error(
                    self.request,
                    'Usuário não encontrado com base no email informado'
                )
                return render(self.request, 'perfil/password_reset.html', {'form': form})            
        else:
            messages.error(
                self.request,
                'Email não foi informado ou está inválido'
            )
            return render(self.request, 'perfil/password_reset.html', {'form': form})

class Code_Verification(View):

    def get(self, *args, **kwargs):        
        return render(self.request, 'perfil/code_validation.html')  

    def post(self, *args, **kwargs):
        codigo = self.request.POST.get('codigo')
        uidb64 = self.request.session.get('uidb64')
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if user is not None:
            password_reset_code = PasswordResetCode.objects.get(codigo=codigo)
            
            if default_token_generator.check_token(user, password_reset_code.token):
                return redirect('perfil:reset_password') 
            else:
                messages.error(
                    self.request,
                    'Token inválido ou o tempo de expiração está vencido'
                )
                return render(self.request, 'perfil/code_validation.html')  
        else:           
            
            context['mensagem_retorno'] = 'Usuário não encontrado, favor repita o processo ou entre em contato com a gente'
            messages.error(
                self.request,
                context['mensagem_retorno']
            )
            return render(self.request, 'perfil/code_validation.html', context)  

class Reset_password(View):
    
    def get(self, *args, **kwargs):
        uidb64 = self.request.session.get('uidb64')
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=uid)
        form = SetPasswordForm(user)
        return render(self.request, 'perfil/reset_password.html', {'form': form})   

    def post(self, *args, **kwargs):
        try:
            new_password = self.request.POST.get('new_password')
            confirm_password = self.request.POST.get('confirm_password')
            uidb64 = self.request.session.get('uidb64')
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=uid)

            """
            if(confirm_password != new_password):
                messages.error(
                    self.request,
                    'A confirmação da senha não confere com a senha informada, as duas precisam ter o mesmo valor'
                )
                return redirect('perfil:reset_password') 
            """
            try:
                password_reset_code = PasswordResetCode.objects.get(usuario=user)
                token = password_reset_code.token

                if user is not None and default_token_generator.check_token(user, token):
                        form = SetPasswordForm(user, self.request.POST)
                        if form.is_valid():
                            user.set_password(form.cleaned_data['new_password1'])
                            user.save()
                            PasswordResetCode.objects.filter(usuario=user).delete()

                            return redirect('perfil:login')
                        else:
                            messages.error(
                                self.request,
                                form.errors
                            )
                            form = SetPasswordForm(user)
                            return render(self.request, 'perfil/reset_password.html', {'form': form})                
                else:
                    return render(self.request, 'perfil/reset_password.html', {'error': 'Token inválido ou expirou.'})
            except PasswordResetCode.DoesNotExist:
                messages.error(
                    self.request,
                    'Token não encontrado com o código informado, por favor tente novamente ou entre em contato com nosso suporte'
                )
        except Exception as e:
            return render(self.request, 'perfil/reset_password.html', {'error': f'Ocorreu um erro.'})
