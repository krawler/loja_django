from django.shortcuts import render, redirect
from django.core import serializers
from django.views import View
from django.urls import reverse
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from produto.models import Variacao, Produto
from produto.produto_service import ProdutoService
from . import pedido_service 
from .models import Pedido, ItemPedido
from perfil.models import PerfilUsuario
from .email.py_email import PyEmail 
from datetime import datetime, timezone, timedelta
import mercadopago
import requests     
import json 


class DispachLoginRequired(View):
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("perfil:login")

        self.produtos_autocomplete = ProdutoService().get_all_product_names()    
    
        return super().dispatch(*args, **kwargs)
    
    def get_query_set(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.filter(usuario=self.request.user)
        return qs


class Pagar(DispachLoginRequired, View):
    
   
    def get(self, *args, **kwargs):

        carrinho = self.request.session.get('carrinho')
        preco_frete = self.request.GET.get('frete')
        self.request.session["preco_frete"] = preco_frete
        
        if carrinho is None:
            return redirect('pedido:compraconcluida') 
        
        carrinho_variacao_ids = [v for v in carrinho]
        bd_variacoes = list(
            Variacao.objects.select_related('produto').filter(id__in=carrinho_variacao_ids)
        )
        
        for variacao in bd_variacoes:
            vid = variacao.id
            svid = str(vid)
            estoque = ProdutoService().getEstoqueAtual(vid)
            qtd_carrinho = int(carrinho[svid]['quantidade'])
            preco_unt = carrinho[svid]['preco_quantitativo']
            preco_unt_promo = carrinho[svid]['preco_quantitativo_promocional']
            variacao = Variacao.objects.get(id=vid)

            if estoque < 1:
                del self.request.session['carrinho'][svid]
                messages.error(
                    self.request,
                    f'O produto {variacao.produto.nome}, {variacao.nome}'
                    ' foi removido do seu carrinho por que o saldo desse produto em nosso estoque foi zerado,'
                    ' você pode solicitar para ser avisado quando esse produto voltar na página do produto'
                    ' ou verificar outras variações'
                )
                self.request.session.save()
                return redirect('produto:carrinho')

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
        
        return redirect("pedido:salvarpedido")

    def post(self, *args, **kwargs):
       
        sdk = mercadopago.SDK('TEST-6359455923298195-121717-ef84e13d4890009bae8c56d3904036df-68852210')

        request_options = mercadopago.config.RequestOptions()
        request_options.custom_headers = {
            'x-idempotency-key': '<SOME_UNIQUE_VALUE>'
        }

        payment_data = {
            "transaction_amount": 4, #self.request.POST.get("transaction_amount"),
           # "token": 'TEST-6359455923298195-121717-ef84e13d4890009bae8c56d3904036df-68852210',
            "description": "testando pagamento em sandbox",
            "installments": 1, #self.request.POST.get("installments"),
            "payment_method_id": "visa", #self.request.POST.get("payment_method_id"),
            "payer": { 
                    "email":   "august.rafael@gmail.com",        #self.request.POST.get("cardholderEmail"),
                    "identification": {
                        "type":  "CPF", #self.request.POST.get("identificationType"),
                        "number": "35982316873" #request.POST.get("identificationNumber")
                    },
                    "first_name": "Rafael A Ramos" #request.POST.get("cardholderName")
            }
        }

        payment_response = sdk.payment().create(payment_data)
        payment = payment_response["response"]

        print(payment)


class SalvarPedido(View):    
    
    def get(self, *args, **kwargs):
        
        preco_frete = self.request.session.get("preco_frete")
        carrinho = self.request.session.get('carrinho')
        if carrinho is None:
            return redirect('pedido:compraconcluida') 
             
        qtd_total_carrinho = sum([int(item['quantidade']) for item in carrinho.values()])
        valor_total_carrinho = sum(
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

        for v in carrinho.values():
            ProdutoService().salvar_saida_produto(variacao=Variacao.objects.filter(id=v['variacao_id']).first(),
                                                  preco_final=v['preco_quantitativo_promocional'],
                                                  quantidade=v['quantidade'],
                                                  user=self.request.user,
                                                  data=datetime.today(),
                                                  hora=datetime.now(),
                                                  pedido=pedido)
        
        self.request.session['pedido_id'] = pedido.id 
        
        ProdutoService().limpa_session_carrinho_user(self.request.user)
        
        url_payment = pedido_service.Pedido_Service().checkout_pagseguro(self.request, pedido.id, preco_frete)
                
        if url_payment is not None and url_payment != '':
            return redirect(url_payment)
               

class CompraConcluida(DispachLoginRequired, View):
    
    def get(self, *args, **kwargs):
        
        del self.request.session['carrinho']  
        id_pedido =  self.request.session.get('pedido_id')   
        pedido = Pedido.objects.get(id=id_pedido)          
        produtos_mais_vendidos = ProdutoService().get_produtos_mais_acessados_por_geral()
        categorias = ProdutoService().get_all_categorias()
        contexto = {                   
                    'pedido': pedido, 
                    'produtos_mais_vendidos': produtos_mais_vendidos,
                    'produtos_autocomplete' : self.produtos_autocomplete,
                    'categorias' : categorias 
                    }       
        if not self.request.session.get("email_enviado"):
            py_email = PyEmail(pedido.usuario.email)
            py_email.set_body(username=self.request.user, nro_pedido=id_pedido, request=self.request)
            py_email.enviar()
            self.request.session["email_enviado"] = True

        return render(self.request, 'pedido/compraconcluida.html', contexto)


class MeusPedidos(DispachLoginRequired, ListView):  
    model = Pedido
    template_name = 'pedido/lista.html'
    paginate_by = 10
    ordering = ['-id']
    
    def get(self, *args, **kwargs):
        usuario = self.request.user
        pedidos = Pedido.objects.filter(usuario=usuario).order_by('id').reverse()
        produtos_mais_vendidos = ProdutoService().get_produtos_mais_acessados_por_geral()
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
    produtos_mais_vendidos = ProdutoService().get_produtos_mais_acessados_por_geral()
    context_object_name = 'pedido'
    template_name = 'pedido/detalhe.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produtos_mais_vendidos'] = self.produtos_mais_vendidos     
        return context


class Tabela(DispachLoginRequired, ListView):
    model = Pedido
    template_name = 'pedido/tabela.html'
    context_object_name = 'pedidos'
    ordering = ['-id']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagina_tabela'] = True
        context['url_delete'] = reverse('pedido:desativar')
        pedidos = context['pedidos']
        pedidos = Pedido.objects.filter(desativado=False).order_by('id').reverse()
        for pedido in pedidos:  
            try:          
                perfil = PerfilUsuario.objects.get(usuario=pedido.usuario)
                pedido.perfil_data = perfil
                data_ultima_compra = pedido_service.Pedido_Service().get_data_ultimo_pedido(user=pedido.usuario)
                pedido.data_ultima_compra = data_ultima_compra
            except PerfilUsuario.DoesNotExist:
                pass    
        context['pedidos'] = pedidos
        return context


class Atualizar_Pedido(DispachLoginRequired, View):
    
    def post(self, *args, **kwargs):
        pedido_id = self.request.POST.get('pedidoid')
        de = self.request.POST.get('get')
        para = self.request.POST.get('para')
        para = pedido_service.Pedido_Service().get_sigla_status(para)
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.status = para
        pedido.save()
        return redirect('pedido:admin_detalhe', pedido_id)


class Desativar_Pedido(View):
    
    def post(self, *args, **kwargs):
        pedido_id = self.request.POST.get('pedidoid')
        pedido = pedido_service.Pedido_Service().desativar_pedido(pedidoid=pedido_id)
        json_data = pedido.desativado
        return JsonResponse(json_data, safe=False)


class ItensPedido_json(ListView):
    
    def get(self, *args, **kwargs):
        pedido_id = self.request.GET.get('pedidoid')
        produtos = pedido_service.Pedido_Service().getItemsProdutos(pedido_id=pedido_id)
        json_data = serializers.serialize('json', produtos)
        return JsonResponse(json_data, safe=False)


class Admin_detalhe_pedido(DispachLoginRequired, View):
    
    def get(self, *args, **kwargs):
        
        pk_url_kwarg = 'pk'
        pedido_id = kwargs['pk']
        pedido = Pedido.objects.filter(id=pedido_id).first()
        perfil = PerfilUsuario.objects.filter(usuario=pedido.usuario).first()
        context = {
            'pedido' : pedido,
            'perfil' : perfil
        }
        return render(self.request, 'pedido/admin/detalhe.html', context)

    def post(self, *args, **kwargs):
        codigo_rasteio = self.request.POST.get('codigo_rastreio')
        id_pedido = self.request.POST.get('id_pedido')
        observacoes = self.request.POST.get('observacoes')
        
        if id_pedido is None:
            return redirect('pedido:tabela')

        if codigo_rasteio or observacoes is not None:
            pedido = Pedido.objects.get(id=id_pedido)
            pedido.codigo_rastreio_correio = codigo_rasteio
            pedido.observacoes = observacoes
            pedido.save()
        
        return redirect('pedido:admin_detalhe', id_pedido)