from django.views import View
import requests
from pedido.models import ItemPedido
from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Q, Count, QuerySet, Sum
from django.core import serializers
from decimal import Decimal
from datetime import datetime
from django.utils import timezone

from perfil.models import Configuracao, PerfilUsuario
from .models import MotivoSaidaProduto, Produto, SessaoCarrinho, Variacao, SaidaProduto, AvisoProdutoDisponivel 
from .models import EntradaProduto, AcessoProduto, ProdutoMaisAcessado, Categoria
import json

class ProdutoService():

    def cart_total_preco(self, carrinho):
        return sum(
            [
                float(item.get('preco_quantitativo_promocional'))
                if item.get('preco_quantitativo_promocional')
                else 
                float(item.get('preco_quantitativo'))
                for item in carrinho.values()
            ]
        ) 


    def get_produtos_mais_vendidos(self):
        '''
        agg_count_pedidos = ItemPedido.objects.values('produto_id').annotate(num_pedidos=Count('id')).order_by('-num_pedidos')[:4]
        itens = list(agg_count_pedidos)
        id_produtos = []
        for item in itens:
            id_produtos.append(item['produto_id'])
        return Produto.objects.filter(id__in=id_produtos)
    '''

    def insert_item_session_carrinho(self, sessao_carrinho, user):
    
        variacao_sessao = Variacao.objects.filter(id=sessao_carrinho['variacao_id']).first()
        usuario = User.objects.filter(username=user).first()
        if not user.is_anonymous:
            variacao_user_sessao = SessaoCarrinho.objects.filter(Variacao=variacao_sessao, user=usuario).first()
            if variacao_user_sessao is None:
                sessao = SessaoCarrinho()
                sessao.Variacao = variacao_sessao
                sessao.user = usuario
                sessao.preco = sessao_carrinho['preco_unitario']
                sessao.preco_promocional = sessao_carrinho['preco_unitario_promocional']
                sessao.quantidade = sessao_carrinho['quantidade']             
                sessao.preco_quantitativo = sessao_carrinho['preco_quantitativo']
                sessao.preco_quantitativo_promocional = sessao_carrinho['preco_quantitativo_promocional']
                sessao.slug = sessao_carrinho['slug']
                sessao.save()
            else:
                variacao_user_sessao.quantidade = sessao_carrinho['quantidade']
                variacao_user_sessao.save()              

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

    def getEstoqueAtual(self, variacao_id):

        entrada_total = EntradaProduto.objects.filter(variacao_id=variacao_id).aggregate(total_entrada=Sum('quantidade'))['total_entrada']

        saida_total = SaidaProduto.objects.filter(variacao_id=variacao_id).aggregate(total_saida=Sum('quantidade'))['total_saida']

        entrada_total = 0 if entrada_total is None else entrada_total        
        saida_total = 0 if saida_total is None else saida_total    

        saldo = entrada_total - saida_total
        
        return saldo


    def get_saldo_estoque_variacoes(self, produto):
        saldos = {}
        variacoes = Variacao.objects.filter(produto=produto)
        for variacao in variacoes:
            saldos[variacao.id] = self.getEstoqueAtual(variacao.id)
        
        return saldos 

    def get_dimensoes_variacoes(self, produto):
        dimensoes = []
        variacoes = Variacao.objects.filter(produto=produto)
        for variacao in variacoes:
            dimensoes.append({
                "id"  : variacao.id,
                "peso" : variacao.peso,
                "largura" : variacao.largura,
                "comprimento" : variacao.comprimento,
                "altura" : variacao.altura
            })
        
        return dimensoes    


    def salvar_categoria(self, nome, id, ativo_menu):
        datahora_criacao = datetime.now()
        if id != None and id != '':
            categoria = Categoria.objects.filter(id=id).first()
            categoria.nome = nome
            categoria.ativo_menu = ativo_menu
            categoria.datahora_criacao = datahora_criacao
        else:    
            categoria = Categoria(nome=nome, datahora_criacao=datahora_criacao, ativo_menu=ativo_menu)
        categoria.save()


    def salvar_acesso_produto(self, user, slug):
    
        produto = Produto.objects.filter(slug=slug).first()
        if produto is not None:
            acesso = AcessoProduto(produto=produto, user=user)
            acesso.save()


    def salvar_aviso_produto_disponivel(self, user, id_variacao):
        variacao = Variacao.objects.get(id=id_variacao)
        aviso_produto = AvisoProdutoDisponivel(variacao=variacao, user=user)
        aviso_produto.save()
        return True;


    def get_produtos_mais_acessados_por_usuario(self, user):
        user = User.objects.filter(username=user).first()
        if user == None:
            return
        with connection.cursor() as cursor:
            str_sql = """
                       SELECT distinct p.nome, p.descricao, p.imagem, p.slug,COUNT(ap.id) AS total_acessos,
                       (SELECT v.preco from produto_variacao v where v.produto_id = p.id order by v.preco asc limit 1) as preco,
                       (SELECT v.preco_promocional from produto_variacao v where v.produto_id = p.id order by v.preco_promocional asc limit 1) as preco_promocional
                        FROM produto_acessoproduto ap
                        INNER JOIN produto_produto p ON ap.produto_id = p.id
                        WHERE ap.user_id = %s
                        GROUP BY p.id
                        ORDER BY total_acessos DESC
                        LIMIT 8
                        """
            cursor.execute(str_sql, [user.id])

            rows = cursor.fetchall()
            produtos = []
            for row in rows:
                produtos.append(ProdutoMaisAcessado(nome=row[0], descricao=row[1], imagem=row[2], 
                                                    slug=row[3], preco=row[4], preco_promocional=row[5], 
                                                    total_acessos=row[6]))

        return produtos


    def get_produtos_mais_acessados_por_geral(self):
        
        with connection.cursor() as cursor:
            str_sql = """
                        SELECT p.nome, p.descricao, p.imagem, p.slug, p.preco_marketing, 
                        p.preco_marketing_promocional, COUNT(ap.id) AS total_acessos
                        FROM produto_acessoproduto ap
                        INNER JOIN produto_produto p ON ap.produto_id = p.id
                        GROUP BY p.id
                        ORDER BY random()
                        LIMIT 8;
                        """
            cursor.execute(str_sql)

            rows = cursor.fetchall()
            produtos = []
            for row in rows:
                produtos.append(ProdutoMaisAcessado(nome=row[0], descricao=row[1], imagem=row[2], 
                                                    slug=row[3], preco=row[4], preco_promocional=row[5], 
                                                    total_acessos=row[6]))

        return produtos


    def get_all_product_names(self):
        produtos = Produto.objects.only('nome')
        produtos = list(produtos)
        return produtos


    def get_all_categorias(self):
        categorias = Categoria.objects.all()
        return categorias

    def salvar_motivo_saida_produto(self, id_motivo, descricao, user):
        if id_motivo != None and id_motivo != '':
            motivo = MotivoSaidaProduto.objects.get(id=id_motivo)
            motivo.descricao = descricao
        else:    
            motivo = MotivoSaidaProduto(descricao=descricao, user=user)
        motivo.save()    
        
    def get_lista_frete_superfrete(self, perfil, request, config):
        
        url = config.url_superfrete
        #bearer_token = config.token_superfrete
        carrinho = request.session['carrinho']
        
        total_with, total_length, total_height, total_weight = 0, 0, 0, 0
        for variacao_id in carrinho:
            variacao = Variacao.objects.get(id=variacao_id)  
            total_with += variacao.largura
            total_length += variacao.comprimento
            total_height += variacao.altura
            total_weight += variacao.peso 
            
        product_package =  {
                "width": total_with,
                "height": total_height,
                "length": total_length,
                "weight": total_weight
            }
        
        perfil = PerfilUsuario.objects.get(usuario=request.user)    
        data = {
            "from" : {
                "postal_code": config.cep_loja,
            },
            "to" : {
              "postal_code" : perfil.cep,  
            }, 
            "services": "1,2",
            "options": {
                "own_hand": False,
                "receipt": False,
                "insurance_value": 0,
                "use_insurance_value": False
            },
            "package": product_package
            
        }
        headers = { 
                   # "Authorization" : bearer_token,
                    "Content-Type" : "application/json",
                    "Accept" : "application/json",
                    "User-Agent": "Superfrete (integracao@superfrete.com)" 
                }
        try:
            response = requests.post(url, headers=headers, json=data)
            print(response.json())
            return response.json()
        except Exception as error:
            print(error)

    def get_lista_frete_melhorenvio(self, perfil, request, config):
            
            url = config.url_melhor_envio
            carrinho = request.session['carrinho']
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

            perfil = PerfilUsuario.objects.get(usuario=request.user) 
            data = {
                "from" : {
                    "postal_code": config.cep_loja,
                },
                "to" : {
                "postal_code" : perfil.cep,  
                }, 
                "products" : products
            }
            headers = { 
                        "Authorization" :  config.token_melhor_envio,
                        "Content-Type" : "Application/json",
                        "Accept" : "Application/json"
                    }
            try:
                response = requests.post(url, headers=headers, json=data)
                return response.json()
            except Exception as error:
                print(error)
