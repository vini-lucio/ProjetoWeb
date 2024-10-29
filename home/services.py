from utils.oracle.conectar import executar_com_cabecalho


def get_tabela_precos() -> list | None:
    """Retorna tabela de preços atualizada"""
    sql = """
        SELECT
            CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END AS C,
            PRODUTOS.CODIGO,
            PRODUTOS_JOBS_CUSTOS.PRECO_ICMS0 AS PRECO_TABELA,
            UNIDADES.UNIDADE,
            CLASSE_IPI.IPI AS IPI,
            PRODUTOS.MULTIPLICIDADE,
            PRODUTOS.PESO_LIQUIDO,
            UNIDADES.UNIDADE AS UNIDADE_PESO

        FROM
            COPLAS.PRODUTOS_JOBS_CUSTOS,
            COPLAS.CLASSE_IPI,
            COPLAS.PRODUTOS,
            COPLAS.UNIDADES

        WHERE
            UNIDADES.CHAVE = PRODUTOS.CHAVE_UNIDADE AND
            CLASSE_IPI.CHAVE = PRODUTOS.CHAVE_CLASSEIPI AND
            PRODUTOS.CPROD = PRODUTOS_JOBS_CUSTOS.CHAVE_PRODUTO AND
            PRODUTOS.FORA_DE_LINHA = 'NAO' AND
            PRODUTOS.CHAVE_FAMILIA IN (7767, 7766, 8378) AND
            PRODUTOS_JOBS_CUSTOS.CHAVE_JOB = 22 AND
            PRODUTOS.DESENVOLVIMENTO = 'NAO' AND
            PRODUTOS_JOBS_CUSTOS.PRECO_ICMS0 > 0 AND

            PRODUTOS.CHAVE_LINHA != 7927 AND
            PRODUTOS.CODIGO NOT LIKE 'ITEM INATIVO%' AND
            PRODUTOS.CODIGO NOT LIKE '*%' AND
            PRODUTOS.CODIGO NOT LIKE '%*' AND
            PRODUTOS.CODIGO NOT LIKE '%AMOSTRA%' AND
            PRODUTOS.DESCRICAO NOT LIKE '%AMOSTRA%' AND
            PRODUTOS.CODIGO NOT LIKE '% UN.%' AND
            PRODUTOS.CODIGO NOT LIKE 'UN %' AND
            PRODUTOS.CODIGO NOT LIKE 'MA500-40  - UN' AND
            PRODUTOS.CODIGO NOT LIKE 'KIT %' AND
            PRODUTOS.CODIGO NOT LIKE 'MA500-35  - %' AND
            PRODUTOS.CODIGO NOT LIKE 'DALI %' AND
            PRODUTOS.CODIGO NOT LIKE 'WURTH %' AND
            PRODUTOS.CODIGO NOT LIKE 'EX %'

        ORDER BY
            PRODUTOS.CHAVE_FAMILIA,
            PRODUTOS.CODIGO
    """

    resultado = executar_com_cabecalho(sql)

    if not resultado:
        return []

    return resultado
