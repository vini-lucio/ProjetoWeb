from datetime import datetime


def converter_data_django_para_str_ddmmyyyy(data_converter) -> str:
    string = str(data_converter)
    data = datetime.strptime(string, '%Y-%m-%d')
    data_formatada = data.strftime('%d/%m/%Y')
    return data_formatada
