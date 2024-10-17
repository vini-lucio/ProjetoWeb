import oracledb
import platform
from django.conf import settings


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


def executar(sql: str) -> list:
    """Conecta e executa um SQL no banco de dados Oracle"""
    connection = conectar()
    with connection.cursor() as cursor:
        cursor.execute(sql)
        resultado = cursor.fetchall()
    return resultado
