from django.template import Library

register = Library()

@register.filter
def formata_preco(val):
    if isinstance(val, str):
        val = float(val)
    return f'R$ {val:.2f}'.replace('.', ',')

@register.filter
def remove_aspas(val):
    return str(val).replace('"', '')

@register.filter
def cart_total_qtd(carrinho):
    return sum([item['quantidade'] for item in carrinho.values()])

@register.filter
def cart_total_preco(carrinho):
    return sum(
        [
            item.get('preco_quantitativo_promocional')
            if item.get('preco_quantitativo_promocional')
            else 
            item.get('preco_quantitativo')
            for item in carrinho.values()
        ]
    ) 
