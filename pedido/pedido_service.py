import datetime
from django.contrib import messages
from produto.models import ProdutoSimples
from perfil.models import PerfilUsuario
import requests
from .models import ItemPedido
from .models import Pedido
from django.db import connection
from django.shortcuts import reverse, redirect
from datetime import datetime, timezone, timedelta
import json


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

    def checkout_pagseguro(self, request, id_pedido, preco_frete):
        
        url_payment = "" 
        total_length = 0
        total_width = 0
        total_height = 0
        total_weight = 0
        
        user = request.user
        perfil = PerfilUsuario.objects.get(usuario=user)
        if perfil.perfil_endereco:
            if preco_frete is None or preco_frete == 0:
                messages.error(request, "Você precisa selecionar uma forma de envio")
                url_return = reverse("produto:resumodacompra")
                return url_return
            preco_frete = float(preco_frete) * 100
        else:
            preco_frete = 0        
        
        try: 
            pedido = Pedido.objects.get(id=id_pedido)
            now = datetime.now(timezone(timedelta(hours=-3))) 
            new_date = now + timedelta(days=1)
            iso_format = new_date.strftime("%Y-%m-%dT%H:%M:%S%Z")
            parts = iso_format.split("UTC")
            expiration_date = parts[0] + parts[1]
            url = "https://sandbox.api.pagseguro.com/checkouts"
            itens_pedido = ItemPedido.objects.filter(pedido=pedido)
                         
            items = []
            for item in itens_pedido:
                items.append(
                    {
                        "reference_id": str(item.variacao.id),
                        "name": item.variacao.produto.nome + ' - '  + item.variacao.nome,
                        "description": item.variacao.produto.descricao,
                        "quantity": item.quantidade,
                        "unit_amount": int((item.preco if item.preco_promocional is None else item.preco_promocional) * 100),
                        "image_url": "https://raradmco.tx1.fcomet.com/media/produto_imagens/2024/06/camiseta-supernatural-nova-01.jpg"
                    }
                )
                total_length = item.variacao.comprimento if item.variacao.comprimento > total_length else total_length
                total_width  = item.variacao.largura if item.variacao.largura > total_width else total_width
                total_height = item.variacao.altura if item.variacao.altura > total_height else total_height
                total_weight += item.variacao.peso
            
            total_weight = total_weight * 1000          
            box = {
                    "dimensions": {
                        "length": total_length * 100,
                        "width": total_width * 100,
                        "height": total_height * 100
                    },
                    "weight":  total_weight
                }
         
            shipping = {}
            if perfil.perfil_endereco: 
                shipping =   {
                                "address" : {
                                    "street": perfil.endereco,
                                    "number": perfil.numero,
                                    "city": perfil.cidade,
                                    "region_code": perfil.estado,
                                    "country": "BRA",
                                    "postal_code": perfil.cep,
                                    "locality": perfil.bairro
                                },
                                "box": box,
                                "type": "FIXED",
                                "service_type": "PAC",
                                "address_modifiable": not perfil.perfil_endereco,
                                "amount": preco_frete   
                            }
            else:
                shipping =  {
                                "box": box,
                                "type": "CALCULATE",
                                "service_type": "PAC",
                                "address_modifiable": not perfil.perfil_endereco,
                                "amount": preco_frete   
                            }
                               
            headers = {
                "accept": "*/*",
                "Authorization": "Bearer 9d724eb2-b076-4ec6-a3f6-2eb62e3be240f701023145f0bcf5fcf389ad5ee0602f587c-7946-4635-be65-30827c01c169",
                "Content-type": "application/json"
            }
            payload = {
                 "shipping" : shipping,
                "reference_id": id_pedido,
                "expiration_date": expiration_date, #"2025-01-14T19:09:10-03:00",
                "customer_modifiable": True,
                "items": items,  
                "additional_amount": 0,
                "discount_amount": 0,
                "payment_methods": [{"type": "pix"}, {"type": "CREDIT_CARD"}],
                "payment_methods_configs": [
                    {
                        "type": "CREDIT_CARD",
                        "config_options": [{"option": "INSTALLMENTS_LIMIT", "value": 4}],         
                    }
                ],     
                "payment_notification_urls": ["https://raradmco.tx1.fcomet.com/loja-django/compraconcluida"], 
                "redirect_url": "https://raradmco.tx1.fcomet.com/loja-django"
            }
        
            response = requests.post(url, json=payload, headers=headers)   
            response_dict = json.loads(response.text)
            if response.status_code == 400:
                messages.error(request, str(response_dict))  
                url_payment = reverse('produto:resumodacompra')                
            elif response.status_code == 201: 
                pedido.json_request_checkout = response.text
                pedido.id_checkout = response_dict["id"]
                pedido.save()   
                url_payment = response_dict["links"][1]['href']
        except TypeError as e:
            print("Erro de tipo:", e)
            print("Verifique se todos os valores estão sendo passados corretamente.")
        except AttributeError as e:
            print("Erro de atributo:", e)
            print("Verifique se os atributos estão sendo acessados corretamente.")    
        except NameError as e:
            print("Erro no reconhecimento de alguma dependencia:", e)    
        except Exception as e:
            print(e)

        return url_payment