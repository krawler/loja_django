from produto.models import Produto
from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError

import re
from utils.validacpf import valida_cpf

class PerfilUsuario(models.Model):

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(null=True, max_length=100) 
    cpf = models.CharField(max_length=14,null=True, blank=True)
    endereco = models.CharField(null=False, max_length=100)
    numero = models.CharField(max_length=15)
    complemento = models.CharField(max_length=50, null=True, blank=True)
    bairro = models.CharField(max_length=50, null=True, blank=True)
    cep = models.CharField(max_length=9, null=False, blank=True)
    cidade = models.CharField(null=False, max_length=30)
    estado = models.CharField(
        max_length=2,
        default='SP',
        choices=(
            ('AC', 'Acre'),
            ('AL', 'Alagoas'),
            ('AP', 'Amapá'),
            ('AM', 'Amazonas'),
            ('BA', 'Bahia'),
            ('CE', 'Ceará'),
            ('DF', 'Distrito Federal'),
            ('ES', 'Espírito Santo'),
            ('GO', 'Goiás'),
            ('MA', 'Maranhão'),
            ('MT', 'Mato Grosso'),
            ('MS', 'Mato Grosso do Sul'),
            ('MG', 'Minas Gerais'),
            ('PA', 'Pará'),
            ('PB', 'Paraíba'),
            ('PR', 'Paraná'),
            ('PE', 'Pernambuco'),
            ('PI', 'Piauí'),
            ('RJ', 'Rio de Janeiro'),
            ('RN', 'Rio Grande do Norte'),
            ('RS', 'Rio Grande do Sul'),
            ('RO', 'Rondônia'),
            ('RR', 'Roraima'),
            ('SC', 'Santa Catarina'),
            ('SP', 'São Paulo'),
            ('SE', 'Sergipe'),
            ('TO', 'Tocantins'),
        )
    )
    telefone = models.CharField(null=True, max_length=50)
    perfil_endereco = models.BooleanField(default=True)
    
    def __str__(self) :
        return f'{self.usuario}'

    def clean(self):
        error_messages = {}

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

class PasswordResetCode(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=50, unique=False)

class ListaDesejoProduto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True)
    adicionado_em = models.DateTimeField(auto_now_add=True)
    desativado = models.BooleanField(default=False)