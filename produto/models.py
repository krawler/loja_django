from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from PIL import Image
from django.utils.text import slugify 
from django.utils.functional import cached_property
from urllib.parse import urljoin
import os
import django


class Categoria(models.Model):
    nome = models.TextField(max_length=50, null=False)
    desativado = models.BooleanField(default=False)
    datahora_criacao = models.DateTimeField(default=django.utils.timezone.now)
    ativo_menu = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome


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
    ),
    categoria = models.ForeignKey(Categoria, null=True, on_delete=models.SET_NULL)

    @cached_property
    def miniatura_media(self):
        if self.imagem:
            return self.get_thumbnail_url(300)
        return None

    @cached_property
    def miniatura_grande(self):
        if self.imagem:
            return self.get_thumbnail_url(600)
        return None

    def get_thumbnail_url(self, size):
        if not self.imagem:
            return None
        # Construir o caminho completo da imagem original
        img_path = self.imagem.path
        path_img = Produto.get_directory_path(img_path)
        file_name = Produto.get_file_name(img_path)
        thumbnail_path = os.path.join(path_img, str(size), file_name)
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

        # Criar o nome do arquivo da miniatura
        base, ext = os.path.splitext(thumbnail_path)
        thumbnail_name = f"{base}_{size}{ext}"

        # Verificar se a miniatura já existe no cache
        if os.path.exists(thumbnail_name):
            thumbnail_name = ProdutoMaisAcessado.convert_path_to_url(path=thumbnail_name)
            return thumbnail_name

        # Criar a miniatura
        img = Image.open(img_path)
        img.thumbnail((size, size))
        img.save(thumbnail_name, quality=95)
        thumbnail_name = ProdutoMaisAcessado.convert_path_to_url(path=thumbnail_name) 
        
        return thumbnail_name

    def get_file_name(file_path): 
        # Verifica se o caminho do arquivo é absoluto 
        if not os.path.isabs(file_path): 
            # Converte o caminho relativo para absoluto 
            file_path = os.path.abspath(file_path) 
        # Retorna o nome do arquivo 
        return os.path.basename(file_path)

    def get_directory_path(file_path): 
        # Verifica se o caminho do arquivo é absoluto 
        if not os.path.isabs(file_path): 
            # Converte o caminho relativo para absoluto 
            file_path = os.path.abspath(file_path) 
            # Retorna o caminho absoluto do diretório 
        return os.path.dirname(file_path)
        
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
        abstract = True


class Variacao(models.Model):
    
    nome = models.CharField(max_length=255, blank=True, null=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    preco = models.FloatField(default=0)
    preco_promocional = models.FloatField(default=0)
    estoque = models.PositiveBigIntegerField(default=1)
    id_preco_stripe = models.CharField(max_length=50, blank=True, null=True)
    peso = models.FloatField(default=0)
    largura  = models.FloatField(default=0)
    comprimento  = models.FloatField(default=0)
    altura  = models.FloatField(default=0)

    def __str__(self):
        return self.produto.nome + '  -  ' + self.nome

    class Meta:
        verbose_name = 'Variação'
        verbose_name_plural = 'variações'        


class SessaoCarrinho(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    Variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    quantidade = models.PositiveIntegerField(null=False)
    preco = models.FloatField()
    preco_promocional = models.FloatField()
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
    data = models.DateField(django.utils.timezone.now)
    hora = models.TimeField(django.utils.timezone.now)
    desativado = models.BooleanField(default=False)


class SaidaProduto(models.Model):
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    quantidade = models.PositiveIntegerField(null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    preco_final = models.FloatField()
    data = models.DateField(default=django.utils.timezone.now)
    hora = models.TimeField(default=django.utils.timezone.now)
    desativado = models.BooleanField(default=False)
    pedido = models.ForeignKey('pedido.Pedido', null=True, on_delete=models.SET_NULL)


class AcessoProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    data = models.DateField(default=django.utils.timezone.now)
    hora = models.TimeField(default=django.utils.timezone.now)
    desativado = models.BooleanField(default=False)


class AvisoProdutoDisponivel(models.Model):
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    data = models.DateField(default=django.utils.timezone.now)
    hora = models.TimeField(default=django.utils.timezone.now)


class ProdutoMaisAcessado(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(max_length=255)
    imagem = models.ImageField(upload_to='produto_imagens/%Y/%m/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    preco = models.FloatField()
    preco_promocional = models.FloatField(default=0)
    total_acessos = models.IntegerField()
    
    @cached_property
    def miniatura_pequena(self): 
        if self.imagem:
            return Produto.get_thumbnail_url(self, 300)
        return None

    def convert_path_to_url(path): 
        # Defina a URL base do seu servidor 
        base_url = "http://localhost:8000/produto_imagens/" 
        # Extraia o caminho relativo da imagem 
        relative_path = os.path.relpath(path, start="C:\\Users\\Usuario\\projects\\python\\loja_django\\produto_imagens") 
        # Converta o caminho relativo para uma URL 
        url = urljoin(base_url, relative_path.replace("\\", "/")) 
        return url

    class Meta:
        managed = False

class ProdutoCheckout(models.Model):
    id_preco_stripe = models.CharField(max_length=50, blank=True, null=True)
    quantidade = models.IntegerField()

    class Meta:
        managed = False
        abstract = True
    

class ImagemProduto(models.Model):
    variacao = models.ForeignKey(Variacao, on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='produto_imagens/variacoes/%Y/%m/', blank=False, null=False)

    @cached_property
    def miniatura_minuscula(self): 
        if self.imagem:
            return Produto.get_thumbnail_url(self, 150)
        return None