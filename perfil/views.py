from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.views.generic import ListView
from django.views import View
from datetime import datetime
from . import forms
from .models import PerfilUsuario
from produto.models import Produto
from produto.produto_service import ProdutoService
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import copy
import json

class BasePerfil(View):
    
    template_name = 'perfil/criar.html'
    
    def setup(self, *args, **kwargs):
        
        super().setup(*args, **kwargs)
        
        self.carrinho = copy.deepcopy(self.request.session.get('carrinho'), {})
        self.perfil = None

        if self.request.user.is_authenticated:
            self.perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()
            self.usuario = User.objects.filter(username=self.request.user).first()
            #TODO: refatorar
            if self.perfil.data_nascimento:
                data_nasc = datetime.strptime(str(self.perfil.data_nascimento), '%Y-%m-%d').date()
                data_nasc_br = data_nasc.strftime('%d/%m/%Y')
                self.perfil.data_nascimento = data_nasc_br
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

        username = self.userform.cleaned_data.get('username')
        password = self.userform.cleaned_data.get('password')
        email = self.userform.data.get('email')
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
            return redirect('perfil:criar')
        
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