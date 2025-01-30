from datetime import datetime


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
