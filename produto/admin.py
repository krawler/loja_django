from django.contrib import admin
from .models import Produto, Variacao

class ItemVariacaoInline(admin.TabularInline):
    model = Variacao
    extra = 1

class ProdutoAdmin(admin.ModelAdmin):
    display_fields = ['nome', 'descricao_curta', 'preco_marketing', 'preco_marketing_promocional']
    inlines = [
        ItemVariacaoInline
    ]    

# Register your models here.
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(Variacao)

