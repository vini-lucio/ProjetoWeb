from django.db import connection


def executar_django(sql: str, exportar_cabecalho: bool = False, **kwargs) -> list:
    """Conecta e executa um SQL no banco de dados pardão Django.

    Parametros:
    -----------
    :sql (str): com codigo sql
    :exportar_cabecalho (bool, Default Faslse): booleano se é para exportar o cabeçalho da consulta
    :kwargs (dict): com os placeholders definicos no sql {'placeholder': valor, ...}.

    Retorno:
    --------
    :list: se exportar_cabecalho = False, com o resultado do sql

    ou

    :list[dict]: se exportar_cabecalho = True, com o restultado do sql onde as chaves são os cabeçalhos da consulta'"""
    with connection.cursor() as cursor:
        cursor.execute(sql, kwargs)
        resultado = cursor.fetchall()

        if resultado and exportar_cabecalho:
            cabecalho = [cabecalho[0] for cabecalho in cursor.description]  # type:ignore
            resultado = [dict(zip(cabecalho, linha)) for linha in resultado]

    return resultado
