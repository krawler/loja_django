from django.template import Library

register = Library()

@register.filter
def formata_preco(val):
    return f'R$ {val:.2f}'.replace('.', ',')

@register.filter
def remove_aspas(val):
    return str(val).replace('"', '')

@register.filter
def cart_total_qtd(carrinho):
    return sum([item['quantidade'] for item in carrinho.values()])

@register.filter
def cart_total_preco(carrinho):
    #soma_preco = sum([item['preco_quantitativo'] for item in carrinho.values()])
    soma_preco_promocional = sum([item['preco_quantitativo_promocional'] for item in carrinho.values()]) 
    return soma_preco_promocional 
