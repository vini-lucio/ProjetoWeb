import pandas
from datetime import datetime, timedelta
from django.conf import settings
from pathlib import Path


def converter_excel_para_json_temporario(caminho_excel_media):
    """Converte excel para json e retorna o byte stream temporario do json"""
    origem = Path(settings.MEDIA_ROOT / caminho_excel_media).resolve()

    xls = pandas.read_excel(origem)
    json = xls.to_json(orient='records')

    return json


def converter_data_django_para_datetime(data_converter) -> datetime:
    string = str(data_converter)
    data = datetime.strptime(string, '%Y-%m-%d')
    return data


def converter_hora_django_para_datetime(hora_converter) -> datetime:
    string = str(hora_converter)
    hora = datetime.strptime(string, '%H:%M:%S')
    return hora


def converter_data_django_para_str_ddmmyyyy(data_converter) -> str:
    if not data_converter:
        return ''
    data = converter_data_django_para_datetime(data_converter)
    data_formatada = data.strftime('%d/%m/%Y')
    return data_formatada


def somar_dias_django_para_str_ddmmyyyy(data_somar, dias_somar=0) -> str:
    if not data_somar:
        return ''
    data = converter_data_django_para_datetime(data_somar)
    dias = float(dias_somar)
    nova_data = data + timedelta(days=dias)
    nova_data_formatada = nova_data.strftime('%d/%m/%Y')
    return nova_data_formatada


def converter_data_django_para_dia_semana(data_converter) -> str:
    data = converter_data_django_para_datetime(data_converter)
    dias_semana = {
        'Monday': 'Seg',
        'Tuesday': 'Ter',
        'Wednesday': 'Qua',
        'Thursday': 'Qui',
        'Friday': 'Sex',
        'Saturday': 'Sab',
        'Sunday': 'Dom'
    }
    data_formatada = dias_semana[data.strftime('%A')]
    return data_formatada


def converter_hora_django_para_str_hh24mm(hora_converter) -> str:
    hora = converter_hora_django_para_datetime(hora_converter)
    hora_formatada = hora.strftime('%H:%M')
    return hora_formatada


def converter_datetime_para_str_ddmmyy(data_converter) -> str:
    if not data_converter:
        return ''
    data_formatada = data_converter.strftime('%d/%m/%y')
    return data_formatada


def converter_datetime_para_str_ddmmyyyy(data_converter) -> str:
    if not data_converter:
        return ''
    data_formatada = data_converter.strftime('%d/%m/%Y')
    return data_formatada
