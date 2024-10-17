from utils.oracle.conectar import executar


def pedidos_dia() -> float:
    sql = """
        SELECT
            ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END), 2) AS TOTAL

        FROM
            COPLAS.VENDEDORES,
            COPLAS.CLIENTES,
            COPLAS.PRODUTOS,
            COPLAS.PEDIDOS,
            COPLAS.PEDIDOS_ITENS

        WHERE
            PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
            PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND

            PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND
            PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND

            -- hoje
            PEDIDOS.DATA_PEDIDO = TRUNC(SYSDATE) AND
            -- primeiro dia util proximo mes
            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('01/11/2024','DD-MM-YYYY')
    """

    resultado = executar(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def conversao_de_orcamentos():
    """Orçamentos dos ultimos 90 dias"""
    sql = """
        SELECT
            ROUND(SUM(CASE WHEN ORCAMENTOS_ITENS.STATUS='FECHADO' THEN (ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END ELSE 0 END) / SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END) * 100, 2) AS CONVERSAO

        FROM
            COPLAS.ORCAMENTOS,
            COPLAS.ORCAMENTOS_ITENS

        WHERE
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
            ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
            ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
            ORCAMENTOS.DATA_PEDIDO >= SYSDATE - 90
    """

    resultado = executar(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def pedidos_mes() -> float:
    sql = """
        SELECT
            ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END) + DEVOLUCOES.TOTAL, 2) AS TOTAL

        FROM
            (
                SELECT
                    CASE WHEN SUM(NOTAS_ITENS.VALOR_MERCADORIAS) IS NULL THEN 0 ELSE SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)) END AS TOTAL

                FROM
                    (SELECT CHAVE_NOTA, SUM(PESO_LIQUIDO) AS PESO_LIQUIDO FROM COPLAS.NOTAS_ITENS GROUP BY CHAVE_NOTA) NOTAS_PESO_LIQUIDO,
                    COPLAS.PRODUTOS,
                    COPLAS.NOTAS_ITENS,
                    COPLAS.NOTAS

                WHERE
                    NOTAS.CHAVE = NOTAS_PESO_LIQUIDO.CHAVE_NOTA(+) AND
                    NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
                    PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
                    NOTAS.VALOR_COMERCIAL = 'SIM' AND
                    NOTAS.ESPECIE = 'E' AND
                    PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND

                    -- primeiro dia do mes
                    NOTAS.DATA_EMISSAO >= TO_DATE('01/10/2024','DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    NOTAS.DATA_EMISSAO <= TO_DATE('31/10/2024','DD-MM-YYYY')
            ) DEVOLUCOES,
            COPLAS.PRODUTOS,
            COPLAS.PEDIDOS,
            COPLAS.PEDIDOS_ITENS

        WHERE
            PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
            PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
            PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND
            PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
            (
                (
                    -- primeiro dia do mes
                    PEDIDOS.DATA_PEDIDO < TO_DATE('01/10/2024','DD-MM-YYYY') AND
                    -- primeiro dia util do mes
                    PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE('01/10/2024','DD-MM-YYYY') AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('01/11/2024','DD-MM-YYYY')
                ) OR
                (
                    -- primeiro dia do mes
                    PEDIDOS.DATA_PEDIDO >= TO_DATE('01/10/2024','DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    PEDIDOS.DATA_PEDIDO <= TO_DATE('31/10/2024','DD-MM-YYYY') AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('01/11/2024','DD-MM-YYYY')
                )
            )

        GROUP BY
            DEVOLUCOES.TOTAL
    """

    resultado = executar(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])
