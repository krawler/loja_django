from django.contrib import admin
from pedido.models import ItemPedido, Pedido

class ItemPedidoInLine(admin.TabularInline):
    model = ItemPedido
    extra = 1

class PedidoAdmin(admin.ModelAdmin):
    line = [
        ItemPedidoInLine
    ]

admin.site.register(Pedido, PedidoAdmin)
admin.site.register(ItemPedido)