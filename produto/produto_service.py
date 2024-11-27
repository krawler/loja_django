from django.views import View
from pedido.models import ItemPedido
from django.contrib.auth.models import User
from django.db.models import Q, Count, QuerySet
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from produto.models import Produto, SessaoCarrinho, Variacao, SaidaProduto, EntradaProduto

import json

class ProdutoService():

    def get_produtos_mais_vendidos(self):
        agg_count_pedidos = ItemPedido.objects.values('produto_id').annotate(num_pedidos=Count('id')).order_by('-num_pedidos')[:4]
        itens = list(agg_count_pedidos)
        id_produtos = []
        for item in itens:
            id_produtos.append(item['produto_id'])
        return Produto.objects.filter(id__in=id_produtos)
    
    def insert_item_session_carrinho(self, sessao_carrinho, user):
        variacao_sessao = Variacao.objects.filter(id=sessao_carrinho['variacao_id']).first()
        usuario = User.objects.filter(username=user).first()
        if not user.is_anonymous:
            variacao_user_sessao = SessaoCarrinho.objects.filter(Variacao=variacao_sessao, user=usuario).first()
            if variacao_user_sessao is None:
                sessao = SessaoCarrinho()
                sessao.Variacao = variacao_sessao
                sessao.user = usuario
                sessao.quantidade = sessao_carrinho['quantidade']             
                sessao.preco_quantitativo = sessao_carrinho['preco_quantitativo']
                sessao.preco_quantitativo_promocional = sessao_carrinho['preco_quantitativo_promocional']
                sessao.slug = sessao_carrinho['slug']
                sessao.save()
            else:
                variacao_user_sessao.quantidade = sessao_carrinho['quantidade']
                variacao_user_sessao.save()
                #TODO Altera a quantidade
        else:
            print("Anonynous")

    def limpa_session_carrinho_user(self, user):
        if not user.is_anonymous:
            SessaoCarrinho.objects.filter(user=user).delete()

    def delete_item_session_carrinho(self, usuario, variacao):
        SessaoCarrinho.objects.filter(user=usuario, Variacao=variacao).delete()

    def getCarrinhoSessao(self, user):
        return SessaoCarrinho.objects.filter(user=user).all()

    def salvar_saida_produto(self, variacao, preco_final, quantidade, user, data, hora, pedido):
        saida_produto = SaidaProduto(variacao=variacao,
                                    preco_final=preco_final,
                                    quantidade=quantidade,
                                    user=user,
                                    data=data,
                                    hora=hora,
                                    pedido=pedido
        )
        saida_produto.save()

    def salvar_entrada_produto(self, variacao, preco_final, quantidade, user):
        print(variacao)
        model_variacao = Variacao.objects.filter(id=variacao).first()
        data = datetime.today()
        hora = timezone.now()
        entrada_produto = EntradaProduto(variacao=model_variacao,
                                    preco_final=preco_final,
                                    quantidade=quantidade,
                                    user=user,
                                    data=data,
                                    hora=hora)
        entrada_produto.save()