from utils.site_setup import get_site_setup

SITE_SETUP = get_site_setup()
if SITE_SETUP:
    verde = SITE_SETUP.rentabilidade_verde_as_float
    amarelo = SITE_SETUP.rentabilidade_amarela_as_float
    vermelho = SITE_SETUP.rentabilidade_vermelha_as_float
    despesa_adm = SITE_SETUP.despesa_administrativa_fixa_as_float

sugestao_rentabilidade_a_menos = -1.99
sugestao_rentabilidade_a_mais = 3.0


def cor_rentabilidade_css(rentabilidade: float) -> str:
    """Retorna o nome da variavel do css referente a cor da rentabilidade"""

    if rentabilidade >= verde:
        return '--verde-escuro'
    if rentabilidade >= amarelo:
        return '--amarelo-escuro'
    if rentabilidade >= vermelho:
        return '--vermelho-escuro'
    return '--roxo-escuro'


def falta_mudar_cor_mes(mc_mes: float, total_mes: float, rentabilidade_mes: float) -> tuple[float, float, float, str]:
    """Retorna quanto precisa vender [0] em uma determinada rentabilidade [1] para mudar de cor, a porcentagem de quanto falta [2] e a cor que vai mudar [3]"""

    if rentabilidade_mes >= verde:
        falta_valor = (((verde - 0.01) + despesa_adm) * total_mes - 100 * mc_mes) / sugestao_rentabilidade_a_menos
        falta_valor_rentabilidade = (verde - 0.01) + despesa_adm + sugestao_rentabilidade_a_menos
        falta_porcentagem = rentabilidade_mes - verde
        return falta_valor, falta_valor_rentabilidade, falta_porcentagem, 'AMARELO'

    if rentabilidade_mes >= amarelo:
        falta_valor = ((verde + despesa_adm) * total_mes - 100 * mc_mes) / sugestao_rentabilidade_a_mais
        falta_valor_rentabilidade = verde + despesa_adm + sugestao_rentabilidade_a_mais
        falta_porcentagem = verde - rentabilidade_mes
        return falta_valor, falta_valor_rentabilidade, falta_porcentagem, 'VERDE'

    if rentabilidade_mes >= vermelho:
        falta_valor = ((amarelo + despesa_adm) * total_mes - 100 * mc_mes) / sugestao_rentabilidade_a_mais
        falta_valor_rentabilidade = amarelo + despesa_adm + sugestao_rentabilidade_a_mais
        falta_porcentagem = amarelo - rentabilidade_mes
        return falta_valor, falta_valor_rentabilidade, falta_porcentagem, 'AMARELO'

    falta_valor = ((vermelho + despesa_adm) * total_mes - 100 * mc_mes) / sugestao_rentabilidade_a_mais
    falta_valor_rentabilidade = vermelho + despesa_adm + sugestao_rentabilidade_a_mais
    falta_porcentagem = vermelho - rentabilidade_mes
    return falta_valor, falta_valor_rentabilidade, falta_porcentagem, 'VERMELHO'
