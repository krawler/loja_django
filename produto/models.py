from django.db import models
import os
from django.conf import settings
from PIL import Image
from django.utils.text import slugify 

# Create your models here.

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

    def get_preco_formatado(self):
        return f'{self.preco_marketing:.2f}'.replace('.',',')
        get_preco_formatado.short_description = 'Preço'

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

       # max_image_size = 800    
       # if self.imagem:
        #    self.resize(self.imagem, max_image_size)


    def __str__(self):
        return self.nome   



class Variacao(models.Model):
    
    nome = models.CharField(max_length=255, blank=True, null=True)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    preco = models.FloatField()
    preco_promocional = models.FloatField(default=0)
    estoque = models.PositiveBigIntegerField(default=1)

    def __str__(self):
        return self.produto.nome + '  -  ' + self.nome

    class Meta:
        verbose_name = 'Variação'
        verbose_name_plural = 'variações'        
