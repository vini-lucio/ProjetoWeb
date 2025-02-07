from django import template

register = template.Library()


def get_attr(obj, atributo):
    return getattr(obj, atributo, None)


register.filter('get_attr', get_attr)


def multiplicar(valor, valor_2):
    if valor_2 >= 0:
        valor_2 = (valor_2 / 100) + 1
    else:
        valor_2 = 1 + (valor_2 / 100)
    return valor * valor_2


register.filter('multiplicar', multiplicar)
