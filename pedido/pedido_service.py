from produto.models import ProdutoSimples
from .models import Pedido
from django.db import connection

class Pedido_Service():

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Pedido_Service, cls).__new__(cls)
        return cls.instance    

    def getItemsProdutos(self, pedido_id):

        with connection.cursor() as cursor:
            str_sql = """
                        SELECT p.nome nome_produto, pv.nome nome_variacao, pv.preco, 
                        pv.preco_promocional, pv.estoque, ip.quantidade
                        FROM pedido_itempedido ip 
                        INNER JOIN produto_produto p ON p.id = ip.produto_id
                        INNER JOIN produto_variacao pv ON pv.produto_id = ip.produto_id
                        WHERE ip.pedido_id = %s
                        """
            cursor.execute(str_sql, [pedido_id])
            rows = cursor.fetchall()

            produtos = []
            for row in rows:
                produto = ProdutoSimples(nome_produto=row[0], nome_variacao=row[1], preco=row[2], 
                                            preco_promocional=row[3], estoque=row[4], quantidade=row[5])
                produtos.append(produto)
            
            return produtos

    def get_data_ultimo_pedido(self, user):

        usuario_id = user.id

        with connection.cursor() as cursor:
            str_sql = """
                        SELECT p.data_emissao 
                        FROM pedido_pedido p 
                        WHERE p.usuario_id = %s 
                        ORDER BY p.data_emissao DESC LIMIT 1
                        """
            cursor.execute(str_sql, [usuario_id])

            row = cursor.fetchone()
            return row[0]

    def get_sigla_status(self, status):
        
        match status:
            case 'Aprovado': return 'A'
            case 'Criado': return 'C'
            case 'Reprovado': return 'R'
            case 'Preparando': return 'P'
            case 'Enviado': return 'E'
            case 'Finalizado': return 'F'

    def desativar_pedido(self, pedidoid):
        pedido = Pedido.objects.get(id=pedidoid)
        pedido.desativado = True
        pedido.save()
        return pedido