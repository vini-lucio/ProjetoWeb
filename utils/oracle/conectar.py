import oracledb
import platform
from django.conf import settings


def conectar() -> oracledb.Connection:
    """Conectar ao banco de dados oracle com as configurações do settings do django"""
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
