from django.shortcuts import render, get_list_or_404, reverse, redirect, get_object_or_404
from django.core import serializers
from django.core.paginator import Paginator
from django.views.generic.list import ListView
from django.views import View
from django.views.generic.detail import DetailView
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, QuerySet
from produto.models import Produto, Variacao 
from produto.produto_service import ProdutoService
from perfil.models import PerfilUsuario
from pedido.models import ItemPedido
import json
import requests

class DispachProdutosMaisVendidos(View):

    def dispatch(self, *args, **kwargs):
        self.produtos_mais_vendidos = ProdutoService().get_produtos_mais_vendidos()
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos_mais_vendidos'] = self.produtos_mais_vendidos     
        return context
    
class ListaProdutos(DispachProdutosMaisVendidos, ListView):    
    model = Produto
    template_name = 'produto/lista.html' 
    context_object_name = 'produtos'
    paginate_by = 6


class DetalheProduto(DispachProdutosMaisVendidos, DetailView):
    model = Produto
    template_name = 'produto/detalhe.html' 
    context_object_name = 'produto'
    slug_url_kwarg = 'slug'

class AdicionarCarrinho(View):
    def get(self, *args, **kwargs):
        http_referer = self.request.META.get('HTTP_REFERER', reverse('produto:lista'))
        variacao_id = self.request.GET.get('vid')
        qtd_form_param = self.request.GET.get('quantidade')
        
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
        quantidade = qtd_form_param if qtd_form_param is not None else 1 
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
            quantidade_carrinho = float(carrinho[variacao_id]['quantidade'])
            #TODO: pegar quantidade dinamicamente
            quantidade_carrinho += float(quantidade)
            
            if variacao_estoque < int(quantidade_carrinho):
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
                'preco_quantitativo_promocional': preco_unitario_promocional * int(quantidade),
                'preco_quantitativo' : preco_unitario * int(quantidade),
                'imagem' : imagem
            }

        ProdutoService().insert_item_session_carrinho(carrinho[variacao_id], self.request.user)

        self.request.session.save()  

        messages.success(
            self.request,
            f'Produto {produto_nome} {variacao_nome} adicionado no seu carrinho'
        )
        
        return redirect('produto:carrinho')

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
        
        variacao = Variacao.objects.filter(id=variacao_id).first()
        ProdutoService().delete_item_session_carrinho(self.request.user, variacao)
        
        self.request.session.save()
        
        return redirect(http_referer)

class Carrinho(DispachProdutosMaisVendidos, View):
    #TODO: salvar os itens da sessao quando carrega o carrinho
    
    def get(self, *args, **kwargs):
        context = {
            'carrinho': self.request.session.get('carrinho'),
            'produtos_mais_vendidos': self.produtos_mais_vendidos
        }
        return render(self.request, 'produto/carrinho.html', context)

class ResumoDaCompra(View):
    
    #verificar validate do token, transferir para arquivo
    bearer_token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZWU4OWMyMmE1ZTIyNjlmNWQyOTA1MzJiMzVjYzY2ZjMyY2FlMDIyZDM1OGEwMDFmMTNhZGViZTNjN2VjYzBmY2IxNDM1NzAzMDI4MjgxMTMiLCJpYXQiOjE3MTkwMTAzMTIuOTA1NjI3LCJuYmYiOjE3MTkwMTAzMTIuOTA1NjI5LCJleHAiOjE3NTA1NDYzMTIuODkxMDIzLCJzdWIiOiI5YzU3YzA5NS0wZTVhLTRmODEtYjlhOC0yYmM4ZTAzZDI4NzciLCJzY29wZXMiOlsic2hpcHBpbmctY2FsY3VsYXRlIiwiZWNvbW1lcmNlLXNoaXBwaW5nIl19.ZlVxabpqdJe8K_PYL9bo0MaElGo9YwxCCCEaPsA5GLOW_q82syoirhkLUsHg82DZUvLVeJH5W8jGAWyqAp8VxOc22YL-3rLLKiFTLQvsapO1vS9j6C9YXXQx0PXzkvBIknIri--1L5lpaRR9nPj3bp_OQULIOsnYkzI2aJ8H8OQ5XA3HT-b7lEqMOoyrpZbHGNtHXaOYL0NWyFb9Bft2Nbez10oRy5uEPm9svUj6RruLjbRMFIIBkGkdqjpSMtcAwCJCQm8OyDgdLxA16YseXkx6Gc32FkiuB_gaORxw_LckOIgO6z4f15PMkytB_MGsHDT7sIv6pXyd9d11qu_aXjHEXxcWuJ_4QszDmKnfXRQ8JJ4JYmw6F2W18sJSynuaSId2te8Sh3gBIkb-wCUC2e89uYXf33eI40SZ0cIgIHqJ4xd11qWtS-I7TzdDjWWPOILf2wdRwXNwiHr5QVsBIm0eoqmud65I9ttIKL9JTQ_JlT0E0f-4iLV392_LabJ8R9ikQq03AC5JwlhEcg3fogIITWLs3K6MNlxcPooVpSmr97u-1fmuDk_naE2mzCwS_4nI8N3QyufO4q-Vzfi6xEYsvsVhtyufU0sJRq3X9DgwJtupip2VGwmfoLoXmrAEXnCNKwdfdNj9T1ePzVMkWSWWM2wnYsrpLbQLkpNVIOg'
    
    def get_lista_frete_melhorenvio(self, perfil):
        
        url = 'https://melhorenvio.com.br/api/v2/me/shipment/calculate'
        
        perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()    
        data = {
            "from" : {
                "postal_code": "18910066",
            },
            "to" : {
              "postal_code" : perfil.cep,  
            }, 
            "package": {
                "height": 4,
                "width": 12,
                "length": 17,
                "weight": 0.3
            }    
        }
        headers = { 
                    "Authorization" :  self.bearer_token,
                    "Content-Type" : "Application/json",
                    "Accept" : "Application/json"
                  }
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()
        except Exception as error:
            print(error)
    
    def get(self, *args, **kwargs):
        
        if not self.request.user.is_authenticated:
            return redirect('perfil:criar')
        
        perfil = PerfilUsuario.objects.filter(usuario=self.request.user).first()
        if perfil is None:
            messages.error(self.request, 'Usuario sem perfil')
            return redirect('perfil:criar')
        
        if not self.request.session.get('carrinho'):
            messages.error(
                self.request,
                'Carrinho vazio'
            )
            return redirect('produto:lista')
        
        fretes = self.get_lista_frete_melhorenvio(perfil)                       
        
        contexto = {
            'usuario': self.request.user,
            'carrinho': self.request.session['carrinho'],
            'perfil': perfil,
            'fretes': fretes,
            'produtos_mais_vendidos': ProdutoService().get_produtos_mais_vendidos()
        }
        return render(self.request, 'produto/resumodacompra.html', contexto)


class Tabela(ListView):
    model = Produto
    template_name = 'produto/tabela.html'
    context_object_name = 'produtos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['area_sem_produtos'] = True
        return context

class EntradaProduto(View):
    
    def get(self, *args, **kwargs):
        
        context = {
            'area_sem_produtos' : True,  
            'variacoes' : Variacao.objects.select_related('produto')
        }

        return render(self.request, 'produto/entrada.html', context)
    
    def post(self, *args, **kwargs):
        
        quantidade = self.request.POST.get('quantidade')
        preco_final = self.request.POST.get('quantidade')
        id_variacao = self.request.POST.get('id_variacao')
        user = self.request.user
        ProdutoService().salvar_entrada_produto(id_variacao, preco_final, quantidade, user)

        return redirect('produto:tabela')

class Variacoes_json(ListView):
    
    def get(self, *args, **kwargs):
        produto_id = self.request.GET.get('produtoid')
        produto = Produto.objects.filter(id=produto_id).first()
        qs_data = Variacao.objects.filter(produto=produto)
        json_data = serializers.serialize('json', qs_data)
        return JsonResponse(json_data, safe=False)

class Busca(ListaProdutos):
    
    def get_queryset(self, *args, **kwargs):
        termo = self.request.GET.get('termo') or self.request.session.get('termo')
        qs = super().get_queryset(*args, **kwargs)
        
        if not termo:
            return qs
        
        self.request.session['termo'] = termo
        qs = qs.filter(
            Q(nome__icontains=termo) | Q(descricao__icontains=termo) | Q(descricao_longa__icontains=termo)
        )
        
        self.request.session.save()
        return qs
