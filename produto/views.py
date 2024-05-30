from django.shortcuts import get_list_or_404, reverse, redirect, get_object_or_404

from django.views.generic.list import ListView
from django.views import View
from django.views.generic.detail import DetailView
from django.http import HttpResponse
from django.contrib import messages
from produto.models import Produto, Variacao 

class ListaProdutos(ListView):    
    model = Produto
    template_name = 'produto/lista.html' 
    context_object_name = 'produtos'
    paginate_by = 3

class DetalheProduto(DetailView):
    model = Produto
    template_name = 'produto/detalhe.html' 
    context_object_name = 'produto'
    slug_url_kwarg = 'slug'

class AdicionarCarrinho(View):
    def get(self, *args, **kwargs):
        http_referer = self.request.META.get('HTTP_REFERER', reverse('produto:lista'))
        variacao_id = self.request.GET.get('vid')
        
        if not variacao_id:
            messages.error(
                self.request,
                'Produto não existe'
            )
            return redirect(http_referer)
        
        variacao = get_object_or_404(Variacao, id=variacao_id)
        
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
            pass
        else:
            pass
                    
        return HttpResponse(f'{variacao.produto} {variacao.nome}')

class RemoverCarrinho(View):
    def get(self, *args, **kwargs):
        return HttpResponse('Remover carrinho')

class Carrinho(View):
    def get(self, *args, **kwargs):
        return HttpResponse('Carrinho')

class Finalizar(View):
    def get(self, *args, **kwargs):
        return HttpResponse('Finalizar')
