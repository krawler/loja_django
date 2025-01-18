from django.template import Library
from datetime import datetime

register = Library()

@register.filter
def converte_int(val):
    if val != '':
        return int(val)
    return ''       

@register.filter
def formata_preco(val):
    if val != '':
        if isinstance(val, str):
            val = float(val)
    else:
        return 0
    return f'R$ {val:.2f}'.replace('.', ',')

@register.filter
def formata_br_date(val):
    if val != '':
        return val.strftime("%d/%m/%Y")
    return ''    

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
            (float(item.get('preco_quantitativo_promocional')))
            if item.get('preco_quantitativo_promocional')
            else 
            float(item.get('preco_quantitativo'))
            for item in carrinho.values()
        ]
    ) 

@register.filter
def resumir_texto(texto, max_caracteres=80):

    if len(texto) <= max_caracteres:
        return texto

    palavras = texto.split()
    resumo = []
    contador = 0

    for palavra in palavras:
        if contador + len(palavra) + 1 <= max_caracteres:
            resumo.append(palavra)
            contador += len(palavra) + 1
        else:
            break

    return ' '.join(resumo) + '...'


@register.filter
def get_status_extenso(val):
    match val:
        case 'A': return 'Aprovado'
        case 'C': return 'Criado'
        case 'R': return 'Reprovado'
        case 'P': return 'Preparando'
        case 'E': return 'Enviado'
        case 'F': return 'Finalizado'

#TODO: parametrizar
@register.filter
def get_next_step(val):
    match val:
        case 'A': return 'Preparando'
        case 'C': return 'Aprovado'
        case 'R': return 'Finalizado'
        case 'P': return 'Enviado'
        case 'E': return 'Finalizado'
        case 'F': return 'Criado'
        
@register.filter
def formata_int(val):
    if val != '':
        return int(val)
    return ''