from django.db import connection
from django.db import connections


def executar_django(sql: str, exportar_cabecalho: bool = False, **kwargs) -> list:
    """Conecta e executa um SQL no banco de dados default do Django. Passar placeholders do SQL em kwargs placeholder: valor"""
    with connection.cursor() as cursor:
        cursor.execute(sql, kwargs)
        resultado = cursor.fetchall()

        if resultado and exportar_cabecalho:
            cabecalho = [cabecalho[0] for cabecalho in cursor.description]  # type:ignore
            resultado = [dict(zip(cabecalho, linha)) for linha in resultado]

    return resultado


def teste():
    with connections['oracle'].cursor() as cursor:
        cursor.execute("SELECT CPROD FROM COPLAS.PRODUTOS")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    return row
