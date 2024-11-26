from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime
from PIL import Image
from django.utils import timezone
from django.utils.text import slugify 
import os

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(max_length=255)
    descricao_longa = models.TextField()
    imagem = models.ImageField(upload_to='produto_imagens/%Y/%m/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    preco_marketing = models.FloatField()
    preco_marketing_promocional = models.FloatField(default=0)
    tipo = models.CharField(
        default='V', 
        max_length=1, 
        choices=(
            ('V', 'Variável'), 
            ('S', 'Simples'),
        )
    )

    @staticmethod
    def resize(img, new_width=800):
        img_full_path = os.path.join(settings.MEDIA_ROOT, img.name)
        img_pil = Image.open(img_full_path)
        original_width, original_height = img_pil.size

        if original_width <= new_width:
            print('Retornando, largura original menor que nova largura')
            img_pil.close()
            return
        
        new_height = round((new_width - original_height) / original_width) 

        new_img = img_pil.resize((new_width, new_height), Image.LANCZOS)
        new_img.save(
            img_full_path,
            optimize=True,
            quality=50
        )   


    def save(self, *args, **kwargs):
        if not self.slug:
            slug = f'{slugify(self.nome)}-{self.pk}'
            self.slug = slug

        super().save(*args, **kwargs)


    def __str__(self):
        return self.nome   

class ProdutoSimples(models.Model):
    nome_produto = models.CharField(max_length=100)
    nome_variacao = models.CharField(max_length=100)
    preco = models.FloatField(default=0)
    preco_promocional = models.FloatField(default=0)  
    quantidade = models.FloatField(default=0)
    estoque = models.IntegerField()

    class Meta:
        managed = False 

class Variacao(models.Model):
    
    nome = models.CharField(max_length=255, blank=True, null=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    preco = models.FloatField(default=0)
    preco_promocional = models.FloatField(default=0)
    estoque = models.PositiveBigIntegerField(default=1)
    id_preco_stripe = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.produto.nome + '  -  ' + self.nome

    class Meta:
        verbose_name = 'Variação'
        verbose_name_plural = 'variações'        

class SessaoCarrinho(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    Variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    quantidade = models.PositiveIntegerField(null=False)
    preco_quantitativo = models.FloatField()
    preco_quantitativo_promocional = models.FloatField()
    slug = models.TextField(null=True)

    class Meta:
        verbose_name = "Carrinho da sessão salva"
        db_table = "sessao_carrinho"   

class EntradaProduto(models.Model):
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    quantidade = models.PositiveIntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    preco_final = models.FloatField()
    data = models.DateField(default=datetime.now().date())
    hora = models.TimeField(default=timezone.now().time())
    desativado = models.BooleanField(default=False)

class SaidaProduto(models.Model):
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    quantidade = models.PositiveIntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    preco_final = models.FloatField()
    data = models.DateField(default=datetime.now().date())
    hora = models.TimeField(default=timezone.now().time())
    desativado = models.BooleanField(default=False)
    pedido = models.ForeignKey('pedido.Pedido', on_delete=models.CASCADE)