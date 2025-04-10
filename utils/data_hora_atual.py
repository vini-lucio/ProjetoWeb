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


def data_x_dias(x: int, passado: bool):
    if passado:
        data_x_dias = datetime.now() - relativedelta(days=x)
    else:
        data_x_dias = datetime.now() + relativedelta(days=x)
    data_x_dias = datetime(data_x_dias.year, data_x_dias.month, data_x_dias.day).date()
    return data_x_dias


def data_365_dias_atras():
    data_12_meses = datetime.now() - relativedelta(days=365)
    data_12_meses = datetime(data_12_meses.year, data_12_meses.month, data_12_meses.day).date()
    return data_12_meses


def data_inicio_analysis():
    return datetime(2010, 1, 1).date()
