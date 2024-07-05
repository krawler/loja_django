from django.db import models
from django.contrib.auth.models import User
from produto.models import Variacao, Produto

class Pedido(models.Model):
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.FloatField()
    qtd_total = models.FloatField(default=0)
    status = models.CharField(
        default='C',
        max_length=1,
        choices=(
            ('A', 'Aprovado'),
            ('C', 'Criado'),
            ('R', 'Reprovado'),
            ('P', 'Enviado'),
            ('F', 'Finalizado'),
        )
    )

    def __str__(self):
        return f'Pedido N. {self.pk}'


class ItemPedido(models.Model):
   
    pedido   = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    produto  = models.ForeignKey(Produto, on_delete=models.CASCADE)   
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE) 
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    preco_promocional = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantidade = models.PositiveIntegerField()
    imagem = models.CharField(max_length=2000)

    def __str__(self):
        return f'Item do pedido N. {self.pedido}'

    class Meta:
        verbose_name = 'Item do pedido'
        verbose_name_plural = 'Itens do pedido'    