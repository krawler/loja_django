from django.contrib import admin
from .models import Produto, Variacao

class VariacaoAdmin(admin.ModelAdmin):
    display_fields = ['nome','produto','preco','preco_promocional','estoque']
    list_filter = ('produto','estoque',)
    search_fields = ('nome',)
    
class ItemVariacaoInline(admin.TabularInline):
    model = Variacao
    extra = 1   
    

class ProdutoAdmin(admin.ModelAdmin):
    display_fields = ['nome', 'descricao_curta', 'preco_marketing', 'preco_marketing_promocional', 'slug']
    inlines = [
        ItemVariacaoInline
    ]   
    list_filter = ('slug',) 
    search_fields = ('nome',)

# Register your models here.
admin.site.register(Produto, ProdutoAdmin)
admin.site.register(Variacao, VariacaoAdmin)

