from datetime import datetime
from dateutil.relativedelta import relativedelta


def data_hora_atual() -> str:
    """Retorna data e hora atual no formato DD/MM/YYYY HH24:MI:SS"""
    data_hora_atual = datetime.now()
    data_hora_atual_formatado = data_hora_atual.strftime("%d/%m/%y %H:%M:%S")
    return data_hora_atual_formatado


def hoje():
    return datetime.today().date()


def hoje_as_yyyymmdd() -> str:
    """Retorna data atual no formato YYYY-MM-DD"""
    hoje_ = hoje()
    hoje_formatado = hoje_.strftime("%Y-%m-%d")
    return hoje_formatado


def data_x_dias(x: int, passado: bool, sempre_dia_1: bool = False, sempre_mes_1: bool = False):
    """Retorna hoje com mais ou menos x dias. Podendo o retorno ser sempre dia 1 e/ou o mes 1.

    Parametros:
    -----------
    :x [int]: com a quantidade de dias para operação.
    :passado [bool]: boolado se será subtraido ou somado os dias de x.
    :sempre_dia_1 [bool]: boolano se o dia retornado seja sempre 1.
    :sempre_mes_1 [bool]: boolano se o mes retornado seja sempre 1.

    Retorno:
    --------
    :Date: com a data de acordo com os parametros enviados."""
    if passado:
        data_x_dias = datetime.now() - relativedelta(days=x)
    else:
        data_x_dias = datetime.now() + relativedelta(days=x)

    ano = data_x_dias.year
    mes = 1 if sempre_mes_1 else data_x_dias.month
    dia = 1 if sempre_dia_1 else data_x_dias.day

    data_x_dias = datetime(ano, mes, dia).date()
    return data_x_dias


def data_365_dias_atras():
    """Retorna hoje menos 365 dias."""
    data_12_meses = datetime.now() - relativedelta(days=365)
    data_12_meses = datetime(data_12_meses.year, data_12_meses.month, data_12_meses.day).date()
    return data_12_meses


def data_inicio_analysis():
    """Retorna data padrão de inicio do sistema analysis 01/01/2010."""
    return datetime(2010, 1, 1).date()
