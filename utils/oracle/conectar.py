import oracledb
import platform
from django.conf import settings


def conectar() -> oracledb.Connection:
    """Retonar conecção ao banco de dados Oracle com as configurações do settings do Django"""
    oracle_user = settings.ORACLE_USER
    oracle_password = settings.ORACLE_PASSWORD
    oracle_dsn = settings.ORACLE_DSN

    sistema_operacional = platform.system()

    # a linha abaixo é para forçar o modo thick do oracle por causa da senha no padrao antigo do oracle
    if sistema_operacional == 'Windows':
        oracledb.init_oracle_client(lib_dir=r"C:\instantclient_19_24")
    else:
        oracledb.init_oracle_client()

    connection = oracledb.connect(
        user=oracle_user,
        password=oracle_password,
        dsn=oracle_dsn
    )

    return connection


def executar_oracle(sql: str, exportar_cabecalho: bool = False, **kwargs) -> list:
    """Conecta e executa um SQL no banco de dados Oracle.

    Parametros:
    -----------
    :sql (str): com codigo sql
    :exportar_cabecalho (bool, Default Faslse): booleano se é para exportar o cabeçalho da consulta
    :kwargs (dict): com os placeholders definicos no sql {'placeholder': valor, ...}. kwargs pode conter {'codigo_sql': True}, onde o sql não será executado e sim retornado

    Retorno:
    --------
    :list: se exportar_cabecalho = False, com o resultado do sql ou com o codigo sql sem executar

    ou

    :list[dict]: se exportar_cabecalho = True, com o restultado do sql onde as chaves são os cabeçalhos da consulta ou
    com o codigo sql sem executar no dict na chave 'CODIGO_SQL'"""
    codigo_sql = kwargs.pop('codigo_sql', False)

    if codigo_sql:
        if exportar_cabecalho:
            return [{'CODIGO_SQL': sql, },]

        return [sql,]

    connection = conectar()
    with connection.cursor() as cursor:
        cursor.execute(sql, kwargs)
        resultado = cursor.fetchall()

        if resultado and exportar_cabecalho:
            cabecalho = [cabecalho[0] for cabecalho in cursor.description]
            resultado = [dict(zip(cabecalho, linha)) for linha in resultado]

    connection.close()
    return resultado
