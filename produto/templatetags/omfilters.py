from django.template import Library
from datetime import datetime

register = Library()

@register.filter
def formata_preco(val):
    if isinstance(val, str):
        val = float(val)
    return f'R$ {val:.2f}'.replace('.', ',')

@register.filter
def formata_br_date(val):
    return val.strftime("%d/%m/%Y")

@register.filter
def formata_br_hora(val):
    return val.strftime("%H:%M")

@register.filter
def remove_aspas(val):
    return str(val).replace('"', '')

@register.filter
def none_to_blank(val):
    if val is None:
        return "-"
    return val    

@register.filter
def cart_total_qtd(carrinho):
    return sum([int(item['quantidade']) for item in carrinho.values()])

@register.filter
def cart_total_preco(carrinho):
    return sum(
        [
            float(item.get('preco_quantitativo_promocional'))
            if item.get('preco_quantitativo_promocional')
            else 
            float(item.get('preco_quantitativo'))
            for item in carrinho.values()
        ]
    ) 
