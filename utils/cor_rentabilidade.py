from utils.site_setup import get_cores_rentabilidade

sugestao_rentabilidade_a_menos = -1.99
sugestao_rentabilidade_a_mais = 3.0


def cor_rentabilidade_css(rentabilidade: float, subtrair_despesa_adm: bool = False) -> str:
    """Retorna o nome da variavel do css referente a cor da rentabilidade atual.

    Parametros:
    -----------
    :rentabilidade [float]: com a rentabilidade para saber a cor.
    :subtrair_despesa_adm [bool]: boolano se é necessario subtrair a despesa administrativa fixa atual da rentabilidade.

    Retorno:
    --------
    :str: com o nome da variavel do estilo css da cor da rentabilidade."""
    cores = get_cores_rentabilidade()
    verde = cores['verde']
    amarelo = cores['amarelo']
    vermelho = cores['vermelho']

    if subtrair_despesa_adm:
        despesa_adm = cores['despesa_adm']
        rentabilidade -= despesa_adm

    if rentabilidade >= verde:
        return '--verde-rentabilidade'
    if rentabilidade >= amarelo:
        return '--amarelo-rentabilidade'
    if rentabilidade >= vermelho:
        return '--vermelho-rentabilidade'
    return '--roxo-rentabilidade'


def falta_mudar_cor_mes(mc_mes: float, total_mes: float, rentabilidade_mes: float, subtrair_despesa_adm: bool = True) -> tuple[float, float, float, str]:
    """Retorna quanto precisa vender [0] em uma determinada rentabilidade [1] para mudar de cor,
    a porcentagem de quanto falta [2] e a cor que vai mudar [3] no mes.

    Parametros:
    -----------
    :mc_mes [float]: com o valor de margem de contribuição do mes atual.
    :total_mes [float]: com o valor total vendido no mes.
    :rentabilidade_mes [float]: com o valor percentual de margem de contribuição do mes atual.
    :subtrair_despesa_adm [bool]: boolano se é necessario subtrair a despesa administrativa fixa atual da rentabilidade.

    Retorno:
    --------
    :tuple[float, float, float, str]: com quanto precisa vender [0] em uma determinada rentabilidade [1] para mudar de cor, a porcentagem de quanto falta [2] e a cor que vai mudar [3] no mes"""
    cores = get_cores_rentabilidade()
    verde = cores['verde']
    amarelo = cores['amarelo']
    vermelho = cores['vermelho']
    despesa_adm = cores['despesa_adm']

    if subtrair_despesa_adm:
        rentabilidade_mes -= despesa_adm

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
