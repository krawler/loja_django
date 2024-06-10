from django.shortcuts import render, get_list_or_404, reverse, redirect, get_object_or_404
from django.core import serializers
from django.views.generic.list import ListView
from django.views import View
from django.views.generic.detail import DetailView
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from produto.models import Produto, Variacao 
from perfil.models import PerfilUsuario
from pprint import pprint
import json

class ListaProdutos(ListView):    
    model = Produto
    template_name = 'produto/lista.html' 
    context_object_name = 'produtos'
    paginate_by = 6

class DetalheProduto(DetailView):
    model = Produto
    template_name = 'produto/detalhe.html' 
    context_object_name = 'produto'
    slug_url_kwarg = 'slug'

class AdicionarCarrinho(View):
    def get(self, *args, **kwargs):
        http_referer = self.request.META.get('HTTP_REFERER', reverse('produto:lista'))
        variacao_id = self.request.GET.get('vid')
        
        #TODO: testes de sessão, remover
        #self.request.session.clear()
        
        if not variacao_id:
            messages.error(
                self.request,
                'Produto não existe'
            )
            return redirect(http_referer)
        
        variacao = get_object_or_404(Variacao, id=variacao_id)
        variacao_estoque = variacao.estoque
        produto = variacao.produto
        
        produto_id = produto.id
        produto_nome = produto.nome
        variacao_nome = variacao.nome or ''
        preco_unitario = variacao.preco
        preco_unitario_promocional = variacao.preco_promocional
        quantidade = 1
        slug = produto.slug
        imagem = json.dumps(str(produto.imagem))
        
        if variacao.estoque < 1:
            messages.error(
                self.request,
                'Estoque insuficiente'
            )
            return redirect(http_referer)
        
        if not self.request.session.get('carrinho'):
            self.request.session['carrinho'] = {}
            self.request.session.save()
            
        carrinho = self.request.session['carrinho']
        
        if variacao_id in carrinho:
            quantidade_carrinho = carrinho[variacao_id]['quantidade']
            #TODO: pegar quantidade dinamicamente
            quantidade_carrinho += 1
            
            if variacao_estoque < quantidade_carrinho:
                messages.error(
                    self.request,
                    f'Estoque insuficiente para {quantidade_carrinho}x no produto {produto_nome}.' 
                    f'Adicionamos {variacao_estoque}x no seu carrinho'
                )
                quantidade_carrinho = variacao_estoque
            
            carrinho[variacao_id]['quantidade'] = quantidade_carrinho
            carrinho[variacao_id]['preco_quantitativo'] = preco_unitario * quantidade_carrinho
            carrinho[variacao_id]['preco_quantitativo_promocional'] = preco_unitario_promocional * quantidade_carrinho  
        else:
            carrinho[variacao_id] = {
                'produto_id' : produto_id,
                'produto_nome' : produto_nome,
                'variacao_nome' : variacao_nome,
                'variacao_id' : variacao_id,
                'preco_unitario' : preco_unitario,
                'preco_unitario_promocional' : preco_unitario_promocional,
                'quantidade' : quantidade,
                'slug' : slug,
                'preco_quantitativo_promocional': preco_unitario_promocional * quantidade,
                'preco_quantitativo' : preco_unitario * quantidade,
                'imagem' : imagem
            }
                  
        self.request.session.save()  
        
        messages.success(
            self.request,
            f'Produto {produto_nome} {variacao_nome} adicionado no seu carrinho'
        )
        
        return redirect(http_referer)

class RemoverCarrinho(View):
    
    def get(self, *args, **kwargs):
        http_referer = self.request.META.get(
            'HTTP_REFERER',
            reverse('produto:lista')
        )
        variacao_id = self.request.GET.get('vid')
        
        if not variacao_id:
            return redirect(http_referer)
        
        if not self.request.session.get('carrinho'):
            return redirect(http_referer)
        
        if variacao_id not in self.request.session['carrinho']:
            return redirect(http_referer)
        
        carrinho = self.request.session['carrinho'][variacao_id]
        
        messages.success(
            self.request,
            f'Produto {carrinho["produto_nome"]} {carrinho["variacao_nome"]} removido do seu carrinho'
        )
        del self.request.session['carrinho'][variacao_id]
        self.request.session.save()
        
        return redirect(http_referer)

class Carrinho(View):
    
    def get(self, *args, **kwargs):
        context = {
            'carrinho': self.request.session.get('carrinho')
        }
        return render(self.request, 'produto/carrinho.html', context)

class ResumoDaCompra(View):
    
    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('perfil:criar')
        
        perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()
        contexto = {
            'usuario': self.request.user,
            'carrinho': self.request.session['carrinho'],
            'perfil': perfil
        }
        return render(self.request, 'produto/resumodacompra.html', contexto)

class Tabela(ListView):
    model = Produto
    template_name = 'produto/tabela.html'
    context_object_name = 'produtos'

class Variacoes_json(ListView):
    def get(self, *args, **kwargs):
        produto_id = self.request.GET.get('produtoid')
        produto = Produto.objects.filter(id=produto_id).first()
        qs_data = Variacao.objects.filter(produto=produto)
        json_data = serializers.serialize('json', qs_data)
        return JsonResponse(json_data, safe=False)