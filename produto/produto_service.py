from django.views import View
from pedido.models import ItemPedido
from django.db.models import Q, Count, QuerySet
from produto.models import Produto

class ProdutoService():

    def get_produtos_mais_vendidos(self):
        agg_count_pedidos = ItemPedido.objects.values('produto_id').annotate(num_pedidos=Count('id')).order_by('-num_pedidos')[:4]
        itens = list(agg_count_pedidos)
        id_produtos = []
        for item in itens:
            id_produtos.append(item['produto_id'])
        return Produto.objects.filter(id__in=id_produtos)