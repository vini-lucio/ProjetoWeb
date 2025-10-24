from django import template
from utils.cor_rentabilidade import cor_rentabilidade_css as cor_css


register = template.Library()


def get_attr(obj, atributo):
    return getattr(obj, atributo, None)


register.filter('get_attr', get_attr)


def multiplicar_porcentagem(valor, porcentagem):
    """Adiciona ou subtrai uma porcentagem de um valor.

    Exemplos de como enviar porcentagem:

    +50% -> 50

    -10.5% -> -10.5"""
    if porcentagem >= 0:
        porcentagem = (porcentagem / 100) + 1
    else:
        porcentagem = 1 + (porcentagem / 100)
    return valor * porcentagem


register.filter('multiplicar_porcentagem', multiplicar_porcentagem)


def cor_rentabilidade_css(margem_contribuicao) -> str:
    """Retorna o nome da variavel da dor no css da margem de contribuição informada"""
    return cor_css(margem_contribuicao, True)


register.filter('cor_rentabilidade_css', cor_rentabilidade_css)
