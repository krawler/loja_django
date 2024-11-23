from produto.models import ProdutoSimples
from django.db import connection

class Pedido_Service():

    def getItemsProdutos(self, pedido_id):

        with connection.cursor() as cursor:
            str_sql = """
                        SELECT p.nome nome_produto, pv.nome nome_variacao, pv.preco, pv.preco_promocional
                        FROM pedido_itempedido ip 
                        INNER JOIN produto_produto p ON p.id = ip.produto_id
                        INNER JOIN produto_variacao pv ON pv.produto_id = ip.produto_id
                        WHERE ip.pedido_id = %s
                        """
            cursor.execute(str_sql, [pedido_id])
            rows = cursor.fetchall()

            produtos = []
            for row in rows:
                produto = ProdutoSimples(nome_produto=row[0], nome_variacao=row[1], preco=row[2], preco_promocional=row[3])
                produtos.append(produto)
            
            return produtos
