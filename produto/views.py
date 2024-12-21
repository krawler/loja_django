from django.shortcuts import render, get_list_or_404, reverse, redirect, get_object_or_404
from django.core import serializers
from django.core.paginator import Paginator
from django.views.generic.list import ListView
from django.views import View
from django.views.generic.detail import DetailView
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count, QuerySet
from produto.models import Produto, Variacao, Categoria 
from produto.produto_service import ProdutoService
from perfil.models import PerfilUsuario
from pedido.models import ItemPedido
from .serializers import VariacaoSerializer
import json
import requests
import mercadopago

class DispachLoginRequired(View):
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("perfil:login")
    
        return super().dispatch(*args, **kwargs)
    
    def get_query_set(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.filter(usuario=self.request.user)
        return qs

class DispachProdutosMaisVendidos(View):

    def dispatch(self, *args, **kwargs):
        produtos_retorno = ProdutoService().get_produtos_mais_acessados_por_usuario(user=self.request.user)
        if produtos_retorno is None or len(produtos_retorno) < 4:
            self.produtos_mais_vendidos = ProdutoService().get_produtos_mais_acessados_por_geral()
        else:    
            self.produtos_mais_vendidos = produtos_retorno   
        self.produtos_autocomplete = ProdutoService().get_all_product_names()        
        self.categorias = ProdutoService().get_all_categorias()

        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos_mais_vendidos'] = self.produtos_mais_vendidos        
        return context
    
class ListaProdutos(DispachProdutosMaisVendidos, ListView):    
    template_name = 'produto/lista.html' 

    def get(self, *args, **kwargs):
        page = self.request.GET.get('page', 1)
        termo = self.request.GET.get('termo') #or self.request.session.get('termo')
        if termo is not None and termo != '':
            #self.request.session['termo'] = termo
            produtos = Produto.objects.filter(imagem__isnull=False).filter(Q(nome__icontains=termo) | Q(descricao__icontains=termo) | Q(descricao_longa__icontains=termo)).order_by('?')[:9]
        else:
            produtos = Produto.objects.filter(imagem__isnull=False).order_by('?')[:9]
        paginator = Paginator(produtos, per_page=4,allow_empty_first_page=True)
        page_object = paginator.get_page(page)

        context = {
            'produtos': produtos,
            'produtos_mais_vendidos': self.produtos_mais_vendidos,
            'produtos_autocomplete' : self.produtos_autocomplete,
            'categorias' : self.categorias,  
            "page_obj": page_object,
            "is_paginated": True
        }
        return render(self.request, self.template_name, context)


class DetalheProduto(DispachProdutosMaisVendidos, DetailView):
    model = Produto
    template_name = 'produto/detalhe.html' 
    context_object_name = 'produto'
    slug_url_kwarg = 'slug'

    def get(self, *args, **kwargs):

        if kwargs != None and kwargs != '':
            user = self.request.user
            if user.is_authenticated:
                ProdutoService().salvar_acesso_produto(user, kwargs['slug'])
            
            produto = Produto.objects.filter(slug=kwargs['slug']).first()
            dimensoes = ProdutoService().get_dimensoes_variacoes(produto)
            lista_estoque_variacoes = ProdutoService().get_saldo_estoque_variacoes(produto)
        
        context = { 
            'saldo_estoque_variacoes' : json.dumps(lista_estoque_variacoes),
            'produto'       : produto,
            'produtos_mais_vendidos' : self.produtos_mais_vendidos,
            'categorias'       :  self.categorias,
            'dimensoes' : dimensoes
        }

        return render(self.request, self.template_name, context)


    def post(self, *args, **kwargs):

        if kwargs != None and kwargs != '':
            user = self.request.user
            id_variacao = self.request.POST.get('id_variacao')
            if user.is_authenticated:
                ProdutoService().salvar_aviso_produto_disponivel(user, id_variacao)
                json_data = '{true}'
            else:
                json_data = '{false}'    
        return JsonResponse(json_data, safe=False)

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
        variacao_estoque = ProdutoService().getEstoqueAtual(variacao_id)
        produto = variacao.produto
        
        produto_id = produto.id
        produto_nome = produto.nome
        variacao_nome = variacao.nome or ''
        preco_unitario = variacao.preco
        preco_unitario_promocional = variacao.preco_promocional
        quantidade = qtd_form_param if qtd_form_param is not None else 1 
        quantidade = int(quantidade)
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

        for item in carrinho:
            if carrinho.get(item).get("quantidade") < 1:
                messages.error(
                    self.request,
                    'Algum item no carrinho tem quantidade abaixo de 1'
                )
                return redirect('produto:carrinho')

        if variacao_id in carrinho:
            quantidade_carrinho = int(carrinho[variacao_id]['quantidade'])
            quantidade_carrinho += quantidade
            
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
            carrinho[variacao_id]['preco_unitario'] = preco_unitario
            carrinho[variacao_id]['preco_unitario_promocional'] = preco_unitario_promocional
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
                'preco_quantitativo' : preco_unitario * quantidade,
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
    
    def get(self, *args, **kwargs):
        context = {
            'carrinho': self.request.session.get('carrinho'),
            'produtos_mais_vendidos': self.produtos_mais_vendidos,
            'categorias': self.categorias,
            'produtos_autocomplete' : self.produtos_autocomplete
        }
        return render(self.request, 'produto/carrinho.html', context)
    
    def post(self, *args, **kwargs):
        variacao_id = self.request.POST.get('variacaoid')
        quantidade = self.request.POST.get('quantidade')
        carrinho = self.request.session.get('carrinho')
        item_carrinho = carrinho[variacao_id]
        item_carrinho['quantidade'] = quantidade
        item_carrinho['preco_quantitativo_promocional'] = item_carrinho.get('preco_unitario_promocional', 0) * float(quantidade)
        item_carrinho['preco_quantitativo'] = item_carrinho.get('preco_unitario', 0) * float(quantidade)
        carrinho[variacao_id] = item_carrinho
        self.request.session['carrinho'] = carrinho
        json_data = carrinho
        return JsonResponse(json_data, safe=False)

class ResumoDaCompra(DispachProdutosMaisVendidos, View):
    
    #verificar validate do token, transferir para arquivo
    bearer_token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZWU4OWMyMmE1ZTIyNjlmNWQyOTA1MzJiMzVjYzY2ZjMyY2FlMDIyZDM1OGEwMDFmMTNhZGViZTNjN2VjYzBmY2IxNDM1NzAzMDI4MjgxMTMiLCJpYXQiOjE3MTkwMTAzMTIuOTA1NjI3LCJuYmYiOjE3MTkwMTAzMTIuOTA1NjI5LCJleHAiOjE3NTA1NDYzMTIuODkxMDIzLCJzdWIiOiI5YzU3YzA5NS0wZTVhLTRmODEtYjlhOC0yYmM4ZTAzZDI4NzciLCJzY29wZXMiOlsic2hpcHBpbmctY2FsY3VsYXRlIiwiZWNvbW1lcmNlLXNoaXBwaW5nIl19.ZlVxabpqdJe8K_PYL9bo0MaElGo9YwxCCCEaPsA5GLOW_q82syoirhkLUsHg82DZUvLVeJH5W8jGAWyqAp8VxOc22YL-3rLLKiFTLQvsapO1vS9j6C9YXXQx0PXzkvBIknIri--1L5lpaRR9nPj3bp_OQULIOsnYkzI2aJ8H8OQ5XA3HT-b7lEqMOoyrpZbHGNtHXaOYL0NWyFb9Bft2Nbez10oRy5uEPm9svUj6RruLjbRMFIIBkGkdqjpSMtcAwCJCQm8OyDgdLxA16YseXkx6Gc32FkiuB_gaORxw_LckOIgO6z4f15PMkytB_MGsHDT7sIv6pXyd9d11qu_aXjHEXxcWuJ_4QszDmKnfXRQ8JJ4JYmw6F2W18sJSynuaSId2te8Sh3gBIkb-wCUC2e89uYXf33eI40SZ0cIgIHqJ4xd11qWtS-I7TzdDjWWPOILf2wdRwXNwiHr5QVsBIm0eoqmud65I9ttIKL9JTQ_JlT0E0f-4iLV392_LabJ8R9ikQq03AC5JwlhEcg3fogIITWLs3K6MNlxcPooVpSmr97u-1fmuDk_naE2mzCwS_4nI8N3QyufO4q-Vzfi6xEYsvsVhtyufU0sJRq3X9DgwJtupip2VGwmfoLoXmrAEXnCNKwdfdNj9T1ePzVMkWSWWM2wnYsrpLbQLkpNVIOg'
    
    sdk = mercadopago.SDK('TEST-6359455923298195-121717-ef84e13d4890009bae8c56d3904036df-68852210')

    #TODO: Mover para produto_service
    def get_lista_frete_melhorenvio(self, perfil):
        
        url = 'https://melhorenvio.com.br/api/v2/me/shipment/calculate'
        
        carrinho = self.request.session['carrinho']
        products = []
        for variacao_id in carrinho:
            variacao = Variacao.objects.get(id=variacao_id)
            product_package =  {
                "width": variacao.largura,
                "height": variacao.altura,
                "length": variacao.comprimento,
                "weight": variacao.peso,
                "quantity": carrinho[variacao_id]['quantidade'] 
            }
            products.append(product_package)

        perfil = PerfilUsuario.objects.get(usuario=self.request.user)    
        data = {
            "from" : {
                # TODO: Parametrizar
                "postal_code": "18910066",
            },
            "to" : {
              "postal_code" : perfil.cep,  
            }, 
            "products" : products
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
        """
        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': '837243872'
        }

        payment_data = {
            "transaction_amount": 100,
            "token": "CARD_TOKEN",
            "description": "Payment description",
            "payment_method_id": 'visa',
            "installments": 1,
            "payer": {
                "email": 'test_user_123456@testuser.com'
            }
        }
        result = self.sdk.payment().create(payment_data, request_options)
        payment = result["response"]

        print(payment)
        """
        carrinho = self.request.session.get('carrinho')
        for item in carrinho:
            if int(carrinho.get(item).get("quantidade")) < 1:
                messages.error(
                    self.request,
                    'Algum item no carrinho tem quantidade abaixo de 1'
                )
                return redirect('produto:carrinho')

        preference_data = ProdutoService().create_preference_mercadopago(carrinho)
        preference_response = self.sdk.preference().create(preference_data)
        preference = preference_response["response"] 

        if not self.request.user.is_authenticated:
            return redirect('perfil:login')
        
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
            'produtos_mais_vendidos': self.produtos_mais_vendidos,
            'categorias': self.categorias,
            'preference' : preference
        }
        return render(self.request, 'produto/resumodacompra.html', contexto)


class Tabela(ListView):
    model = Produto
    template_name = 'produto/tabela.html'
    context_object_name = 'produtos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagina_tabela'] = True

        return context

class EntradaProduto(DispachLoginRequired, View):
    
    def get(self, *args, **kwargs):
        
        variacoes = Variacao.objects.select_related('produto')
    
        for variacao in variacoes:
            variacao.saldo_estoque = ProdutoService().getEstoqueAtual(variacao.id)

        context = {
            'area_sem_produtos' : True,  
            'variacoes' : variacoes,
            'pagina_tabela' : True
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
        qs_variacoes = Variacao.objects.filter(produto=produto)

        for variacao in qs_variacoes:
            saldo_estoque = ProdutoService().getEstoqueAtual(variacao.id)
            variacao.saldo_estoque = saldo_estoque
            serializer = VariacaoSerializer(qs_variacoes, many=True)
            json_data = json.dumps(serializer.data)
        
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

class CategoriaView(DispachLoginRequired, View):
    
    def get(self, *args, **kwargs):
        
        context = {
            'area_sem_produtos' : True,  
            'categorias' : Categoria.objects.all(),
            'pagina_tabela' : True
        }

        return render(self.request, 'produto/categoria.html', context)
    
    def post(self, *args, **kwargs):
        
        nome = self.request.POST.get('nome')
        ativo_menu = 'ativo_menu' in self.request.POST
        id_categoria = self.request.POST.get('id_categoria')
        ProdutoService().salvar_categoria(nome, id_categoria, ativo_menu)

        return redirect('produto:categoria')