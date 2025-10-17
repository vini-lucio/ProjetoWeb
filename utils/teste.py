import oracledb
import platform

# TODO: Documentar


def teste(oracle_user, oracle_password, oracle_dsn):
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

    with connection.cursor() as cursor:
        cursor.execute("SELECT CODIGO FROM COPLAS.PRODUTOS WHERE CODIGO='CONE3/4'")
        linha = cursor.fetchone()

    print()
    print()
    print()
    print(linha)
    print()
    print()
    print()
