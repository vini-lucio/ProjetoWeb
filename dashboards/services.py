from utils.oracle.conectar import conectar


def teste():
    connection = conectar()
    with connection.cursor() as cursor:
        cursor.execute("SELECT CODIGO FROM COPLAS.PRODUTOS WHERE CODIGO = 'CONE3/4'")
        linha = cursor.fetchall()
    return linha


if __name__ == '__main__':
    teste()
