from produto.models import ProdutoSimples, Variacao
from .models import Pedido
from django.db import connection
from django.shortcuts import reverse
from pagseguro import PagSeguro

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

    def checkout_pagseguro(self, request, carrinho, id_pedido):

        user = request.user
        perfil = user.perfilusuario
        
        '''
        pg = PagSeguro(email="august.rafael@gmail.com", token="9d724eb2-b076-4ec6-a3f6-2eb62e3be240f701023145f0bcf5fcf389ad5ee0602f587c-7946-4635-be65-30827c01c169", config=config)        
        try:
            pg.reference = id_pedido
            pg.sender = {
                "name": "Iza Marina Viccino",
                "area_code": "14",
                "phone": "996064031",
                "email": "iviccino@gmail.com",
            }
            pg.shipping = {
                "type": pg.SEDEX,
                "street": perfil.endereco,
                "number": perfil.numero,
                "complement": perfil.complemento,
                "district": perfil.bairro,
                "postal_code": perfil.cep,
                "city": perfil.cidade,
                "state": perfil.estado,
                "country": "BRA"
            }
            for item in carrinho:
                variacao = Variacao.objects.get(id=item) 
                pg.items.append(
                    {"id": str(variacao.id), 
                        "description": variacao.produto.nome + ' - ' + variacao.nome, 
                        "amount": variacao.preco if variacao.preco_promocional is None else variacao.preco_promocional, 
                        "quantity": 2, 
                        "weight": float(variacao.peso),
                        "shipping_cost": 10.00
                })
            pg.extra_amount = 5.70    
            pg.redirect_url = request.build_absolute_uri(
                                        reverse('pedido:compraconcluida')
            )
            pg.notification_url = request.build_absolute_uri(
                                        reverse('pedido:compraconcluida')  #notification
            )
            response = pg.checkout()
            return response.payment_url
        except TypeError as e:
            print("Erro de tipo:", e)
            print("Verifique se todos os valores estão sendo passados corretamente.")
        except AttributeError as e:
            print("Erro de atributo:", e)
            print("Verifique se os atributos estão sendo acessados corretamente.")    
        except Exception as e:
            print(e)
        '''