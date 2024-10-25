from datetime import datetime


def converter_data_django_para_datetime(data_converter) -> datetime:
    string = str(data_converter)
    data = datetime.strptime(string, '%Y-%m-%d')
    return data


def converter_data_django_para_str_ddmmyyyy(data_converter) -> str:
    data = converter_data_django_para_datetime(data_converter)
    data_formatada = data.strftime('%d/%m/%Y')
    return data_formatada


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
