from rest_framework import serializers
from .models import Variacao
from . import produto_service

class VariacaoSerializer(serializers.ModelSerializer):
    saldo_estoque = serializers.SerializerMethodField()

    class Meta:
        model = Variacao
        fields = '__all__'  # Inclui todos os campos

    def get_saldo_estoque(self, obj):
        return produto_service.ProdutoService().getEstoqueAtual(obj.id)