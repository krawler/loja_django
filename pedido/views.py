from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core import serializers
from django.core.paginator import Paginator
from produto.models import Variacao, Produto
from produto.produto_service import ProdutoService
from .models import Pedido, ItemPedido
from .email.py_email import PyEmail 
from datetime import datetime, date
from pprint import pprint
import stripe

class DispachLoginRequired(View):
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("perfil:criar")
    
        return super().dispatch(*args, **kwargs)
    
    def get_query_set(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.filter(usuario=self.request.user)
        return qs


class Pagar(DispachLoginRequired, View):
    
    stripe.api_key = 'sk_test_51PRDqWFqNwY82ww5DnAS83DgAsvwPRLbVCTtcHDoWXU8G8I4UGy13f5LHXYsQsl3wDlgFSBdRRMzXeILk8Blenhd00BmZJK1Me'
    
    def create_checkout_session(self, variacoes):
        
        #TODO: Falta passar a quantidade do carrinho
            
        line_items = []       
        for variacao in variacoes:
            line_items.append({
                'price': variacao.id_preco_stripe,
                'quantity': 1
            })
            
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                mode='payment',
                success_url='http://localhost:8000/pedido/salvarpedido',
                cancel_url='http://localhost:8000/produto/resumodacompra',
                stripe_account='acct_1PRDqWFqNwY82ww5'
            )
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)
 
    def get(self, *args, **kwargs):
        
        if not self.request.session.get('carrinho'):
            return redirect('produto:resumodacompra')
        
        carrinho = self.request.session.get('carrinho')
        carrinho_variacao_ids = [v for v in carrinho]
        bd_variacoes = list(
            Variacao.objects.filter(id__in=carrinho_variacao_ids)
        )
        return self.create_checkout_session(bd_variacoes)

class SalvarPedido(View):    
    
    def get(self, *args, **kwargs):
        carrinho = self.request.session.get('carrinho')
        if carrinho is None:
            return redirect('pedido:compraconcluida') 
        
        carrinho_variacao_ids = [v for v in carrinho]
        bd_variacoes = list(
            Variacao.objects.select_related('produto').filter(id__in=carrinho_variacao_ids)
        )
        
        for variacao in bd_variacoes:
            vid = variacao.id
            svid = str(vid)
            estoque = variacao.estoque
            qtd_carrinho = int(carrinho[svid]['quantidade'])
            preco_unt = carrinho[svid]['preco_quantitativo']
            preco_unt_promo = carrinho[svid]['preco_quantitativo_promocional']
            
            if estoque < qtd_carrinho:
                carrinho[svid]['quantidade'] = estoque        
                carrinho[svid]['preco_quantitativo'] = estoque * preco_unt
                carrinho[svid]['preco_quantidade_promocional'] = estoque * preco_unt_promo    
                
                messages.error(
                    self.request,
                    'Estoque insuficiente para alguns produtos do seu carrinho. '
                    'Reduzimos a quantidade desses produtos. Por favor, verifique '
                    'em quais produtos foram afetados a seguir'
                )
                self.request.session.save()
                return redirect('produto:carrinho')       
        
        qtd_total_carrinho = sum([int(item['quantidade']) for item in carrinho.values()])
        valor_total_carrinho =  sum(
                                    [
                                        item.get('preco_quantitativo_promocional')
                                        if item.get('preco_quantitativo_promocional')
                                        else 
                                        item.get('preco_quantitativo')
                                        for item in carrinho.values()
                                    ]
                                ) 
        pedido = Pedido(usuario=self.request.user, 
                        total=valor_total_carrinho, 
                        qtd_total=qtd_total_carrinho,
                        status='C',
                        data_emissao=datetime.today(),
                        hora_emissao=datetime.now())   
        pedido.save()
        
         
        ItemPedido.objects.bulk_create([
            ItemPedido(
                pedido=pedido,
                produto=Produto.objects.filter(id=v['produto_id']).first(),
                produto_id=v['produto_id'],
                variacao=Variacao.objects.filter(id=v['variacao_id']).first(),
                preco=v['preco_quantitativo'],
                preco_promocional=v['preco_quantitativo_promocional'],
                quantidade=v['quantidade'],
                imagem=v['imagem']
            ) for v in carrinho.values()
        ])
                                             
        del self.request.session['carrinho']
        ProdutoService().limpa_session_carrinho_user(self.request.user)
        self.request.session['pedido_id'] = pedido.id 
        return redirect('pedido:compraconcluida')        
        

class CompraConcluida(View):
    
    def get(self, *args, **kwargs):
        pedido_id =  self.request.session.get('pedido_id')   
        pedido = Pedido.objects.filter(id=pedido_id).first()
        produtos_mais_vendidos = ProdutoService().get_produtos_mais_vendidos()
        contexto = {                   
                    'pedido': pedido, 
                    'produtos_mais_vendidos': produtos_mais_vendidos
                   }       
        py_email = PyEmail(pedido.usuario.email)
        py_email.set_body(username=self.request.user, nro_pedido=pedido_id, request=self.request)
        py_email.enviar()
        return render(self.request, 'pedido/compraconcluida.html', contexto)
    
class MeusPedidos(DispachLoginRequired, ListView):  
    model = Pedido
    template_name = 'pedido/lista.html'
    paginate_by = 10
    ordering = ['-id']
    
    def get(self, *args, **kwargs):
        usuario = self.request.user
        pedidos = Pedido.objects.filter(usuario=usuario)
        produtos_mais_vendidos = ProdutoService().get_produtos_mais_vendidos()
        page = self.request.GET.get('page', 1)
        paginator = Paginator(pedidos, per_page=10)
        page_object = paginator.get_page(page)
        contexto = {
            'pedidos': pedidos,
            'produtos_mais_vendidos': produtos_mais_vendidos,
            "page_obj": page_object,
            "is_paginated": True
        }
        return render(self.request, self.template_name, contexto)

class Detalhe(DispachLoginRequired, DetailView):

    model = Pedido
    produtos_mais_vendidos = ProdutoService().get_produtos_mais_vendidos()
    context_object_name = 'pedido'
    template_name = 'pedido/detalhe.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos_mais_vendidos'] = self.produtos_mais_vendidos     
        return context

class Tabela(ListView):
    model = Pedido
    template_name = 'pedido/tabela.html'
    context_object_name = 'pedidos'
    ordering = ['-id']

class ItensPedido_json(ListView):
    
    def get(self, *args, **kwargs):
        pedido_id = self.request.GET.get('pedidoid')
        qs_data =  ItemPedido.objects.filter(id=pedido_id)
        json_data = serializers.serialize('json', qs_data)
        return JsonResponse(json_data, safe=False)
