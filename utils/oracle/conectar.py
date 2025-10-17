import oracledb
import platform
from django.conf import settings

# TODO: Documentar


def conectar() -> oracledb.Connection:
    """Conectar ao banco de dados Oracle com as configurações do settings do Django"""
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
    """Conecta e executa um SQL no banco de dados Oracle. Passar placeholders do SQL em kwargs placeholder: valor"""
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
