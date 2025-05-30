from django import template
from utils.cor_rentabilidade import cor_rentabilidade_css as cor_css

register = template.Library()


def get_attr(obj, atributo):
    return getattr(obj, atributo, None)


register.filter('get_attr', get_attr)


def multiplicar_porcentagem(valor, valor_2):
    if valor_2 >= 0:
        valor_2 = (valor_2 / 100) + 1
    else:
        valor_2 = 1 + (valor_2 / 100)
    return valor * valor_2


register.filter('multiplicar_porcentagem', multiplicar_porcentagem)


def dividir_porcentagem(valor, valor_2):
    if not valor_2:
        return 0
    return valor / valor_2 * 100


register.filter('dividir_porcentagem', dividir_porcentagem)


def cor_rentabilidade_css(valor):
    return cor_css(valor, True)


register.filter('cor_rentabilidade_css', cor_rentabilidade_css)
