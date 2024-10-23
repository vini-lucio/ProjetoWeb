from utils.oracle.conectar import executar


def pedidos_dia(primeiro_dia_util_proximo_mes: str) -> float:
    """Valor mercadorias dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
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
            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
    """

    sql = sql.format(primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    resultado = executar(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def rentabilidade_pedidos_dia(despesa_administrativa_fixa: float, primeiro_dia_util_proximo_mes: str) -> float:
    """Rentabilidade dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
    sql = """
        SELECT
            -- despesa administrativa (ultima subtração)
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - {despesa_administrativa_fixa} AS RENTABILIDADE

        FROM
            (
                SELECT
                    ROUND(LFRETE.MC_SEM_FRETE / (SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM))) * 100, 2) AS RENTABILIDADE,
                    ROUND(LFRETE.MC_SEM_FRETE, 2) AS MC_MES,
                    ROUND(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 2) AS TOTAL_MES,
                    ROUND(NVL(LFRETE.MC_SEM_FRETE_PP / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2) AS RENTABILIDADE_PP,
                    ROUND(LFRETE.MC_SEM_FRETE_PP, 2) AS MC_MES_PP,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PP,
                    ROUND(NVL(LFRETE.MC_SEM_FRETE_PT / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2) AS RENTABILIDADE_PT,
                    ROUND(LFRETE.MC_SEM_FRETE_PT, 2) AS MC_MES_PT,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PT,
                    ROUND(NVL(LFRETE.MC_SEM_FRETE_PQ / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2) AS RENTABILIDADE_PQ,
                    ROUND(LFRETE.MC_SEM_FRETE_PQ, 2) AS MC_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PQ

                FROM
                    (
                        SELECT
                            ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

                        FROM
                            (
                                SELECT
                                    VENDEDORES.NOMERED AS CARTEIRA,
                                    PEDIDOS.NUMPED,
                                    PRODUTOS.CHAVE_FAMILIA,
                                    PRODUTOS.CODIGO,
                                    ROUND(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS VALOR_MERCADORIAS,
                                    ROUND(PEDIDOS_ITENS.ANALISE_LUCRO - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS MC,
                                    ROUND(PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS RATEIO_FRETE,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * PEDIDOS_ITENS.ALIQUOTA_IPI / 100, 2) AS IPI,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (CASE WHEN PEDIDOS_ITENS.ANALISE_PIS = 0 THEN 0 ELSE 0.65 END * (1 - (PEDIDOS_ITENS.ICMS_ALIQUOTA * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100))) / 100, 2) AS PIS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (CASE WHEN PEDIDOS_ITENS.ANALISE_COFINS = 0 THEN 0 ELSE 3 END * (1 - (PEDIDOS_ITENS.ICMS_ALIQUOTA * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100))) / 100, 2) AS COFINS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (PEDIDOS_ITENS.ICMS_ALIQUOTA + CASE WHEN CLIENTES.ISENTO_INSCRICAO = 'SIM' AND PEDIDOS_ITENS.DESTINO_MERCADORIAS = 'CONSUMO' THEN (SELECT ALIQUOTA_FCP FROM COPLAS.MATRIZ_ICMS WHERE UF_EMITENTE = UF_DESTINO AND UF_EMITENTE = COALESCE(PLATAFORMAS.UF_ENT, CLIENTES.UF)) ELSE 0 END + CASE WHEN PEDIDOS_ITENS.ANALISE_ICMS_PARTILHA = 0 THEN 0 ELSE (SELECT ALIQUOTA FROM COPLAS.MATRIZ_ICMS WHERE UF_EMITENTE = UF_DESTINO AND UF_EMITENTE = COALESCE(PLATAFORMAS.UF_ENT, CLIENTES.UF)) - PEDIDOS_ITENS.ICMS_ALIQUOTA END) * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100, 2) AS ICMS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS_ITENS.ANALISE_CONTRIBUICAO = 0 THEN 0 ELSE 2 END / 100, 2) AS IR,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS_ITENS.ANALISE_CONTRIBUICAO = 0 THEN 0 ELSE 1.08 END / 100, 2) AS CSLL,
                                    ROUND(CASE WHEN PEDIDOS.VALOR_FRETE_INCL_ITEM = 0 THEN 0 ELSE (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) * PEDIDOS_ITENS.COMISSAO_PADRAO_PERC / 100 END, 2) AS COMISSAO_FRETE_ITEM,
                                    ROUND(CASE WHEN PEDIDOS.VALOR_FRETE_INCL_ITEM = 0 THEN 0 ELSE (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) * PEDIDOS_ITENS.ANALISE_DESPESAS_ADM / PEDIDOS_ITENS.VALOR_TOTAL END, 2) AS DESPESA_ADM_FRETE_ITEM

                                FROM
                                    COPLAS.PLATAFORMAS,
                                    COPLAS.CLIENTES,
                                    COPLAS.VENDEDORES,
                                    COPLAS.PRODUTOS,
                                    COPLAS.PEDIDOS_ITENS,
                                    COPLAS.PEDIDOS

                                WHERE
                                    PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
                                    CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
                                    CLIENTES.CHAVE_VENDEDOR3 = VENDEDORES.CODVENDEDOR AND
                                    PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
                                    PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
                                    PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND

                                    -- hoje
                                    PEDIDOS.DATA_PEDIDO = TRUNC(SYSDATE) AND
                                    -- primeiro dia util do proximo mes
                                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                            )
                    ) LFRETE,
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
                    PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND

                    -- hoje
                    PEDIDOS.DATA_PEDIDO = TRUNC(SYSDATE) AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')

                GROUP BY
                    LFRETE.MC_SEM_FRETE,
                    LFRETE.MC_SEM_FRETE_PP,
                    LFRETE.MC_SEM_FRETE_PT,
                    LFRETE.MC_SEM_FRETE_PQ
            )
    """

    sql = sql.format(despesa_administrativa_fixa=despesa_administrativa_fixa,
                     primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    resultado = executar(sql)

    # não consegui identificar o porque, não esta retornado [(none,),] e sim [], indice [0][0] não funciona
    if not resultado:
        return 0.00

    return float(resultado[0][0])


def conversao_de_orcamentos():
    """Taxa de conversão de orçamentos com valor comercial dos ultimos 90 dias, ignorando orçamentos oportunidade"""
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


def pedidos_mes(primeiro_dia_mes: str, primeiro_dia_util_mes: str,
                ultimo_dia_mes: str, primeiro_dia_util_proximo_mes: str) -> float:
    """Valor mercadorias dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes, debitando as notas de devolução"""
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
                    NOTAS.DATA_EMISSAO >= TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    NOTAS.DATA_EMISSAO <= TO_DATE('{ultimo_dia_mes}','DD-MM-YYYY')
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
                    PEDIDOS.DATA_PEDIDO < TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                    -- primeiro dia util do mes
                    PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE('{primeiro_dia_util_mes}','DD-MM-YYYY') AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                ) OR
                (
                    -- primeiro dia do mes
                    PEDIDOS.DATA_PEDIDO >= TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    PEDIDOS.DATA_PEDIDO <= TO_DATE('{ultimo_dia_mes}','DD-MM-YYYY') AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                )
            )

        GROUP BY
            DEVOLUCOES.TOTAL
    """

    sql = sql.format(primeiro_dia_mes=primeiro_dia_mes, primeiro_dia_util_mes=primeiro_dia_util_mes,
                     ultimo_dia_mes=ultimo_dia_mes, primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    resultado = executar(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def rentabilidade_pedidos_mes(despesa_administrativa_fixa: float, primeiro_dia_mes: str,
                              primeiro_dia_util_mes: str, ultimo_dia_mes: str,
                              primeiro_dia_util_proximo_mes: str) -> dict[str, float]:
    """Rentabilidade dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes"""
    sql = """
        SELECT
            ROUND((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100), 2) AS MC_MES,
            TOTAL_MES,

            -- despesa administrativa (ultima subtração)
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - {despesa_administrativa_fixa} AS RENTABILIDADE

        FROM
            (
                SELECT
                    ROUND((LFRETE.MC_SEM_FRETE + DEVOLUCOES.RENTABILIDADE) / (SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) + DEVOLUCOES.TOTAL) * 100, 2) AS RENTABILIDADE,
                    ROUND(LFRETE.MC_SEM_FRETE + DEVOLUCOES.RENTABILIDADE, 2) AS MC_MES,
                    ROUND(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) + DEVOLUCOES.TOTAL, 2) AS TOTAL_MES,
                    ROUND((LFRETE.MC_SEM_FRETE_PP + DEVOLUCOES.RENTABILIDADE_PP) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PP) * 100, 2) AS RENTABILIDADE_PP,
                    ROUND(LFRETE.MC_SEM_FRETE_PP + DEVOLUCOES.RENTABILIDADE_PP, 2) AS MC_MES_PP,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PP, 2) AS TOTAL_MES_PP,
                    ROUND((LFRETE.MC_SEM_FRETE_PT + DEVOLUCOES.RENTABILIDADE_PT) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PT) * 100, 2) AS RENTABILIDADE_PT,
                    ROUND(LFRETE.MC_SEM_FRETE_PT + DEVOLUCOES.RENTABILIDADE_PT, 2) AS MC_MES_PT,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PT, 2) AS TOTAL_MES_PT,
                    ROUND((LFRETE.MC_SEM_FRETE_PQ + DEVOLUCOES.RENTABILIDADE_PQ) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PQ) * 100, 2) AS RENTABILIDADE_PQ,
                    ROUND(LFRETE.MC_SEM_FRETE_PQ + DEVOLUCOES.RENTABILIDADE_PQ, 2) AS MC_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PQ, 2) AS TOTAL_MES_PQ

                FROM
                    (
                        SELECT
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END) END AS PP,
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.VALOR_MERCADORIAS ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END) END AS PT,
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END) END AS PQ,
                            CASE WHEN SUM(NOTAS_ITENS.VALOR_MERCADORIAS) IS NULL THEN 0 ELSE SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)) END AS TOTAL,
                            CASE WHEN SUM(NOTAS_ITENS.ANALISE_LUCRO) IS NULL THEN 0 ELSE SUM(NOTAS_ITENS.ANALISE_LUCRO) END AS RENTABILIDADE,
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) END AS RENTABILIDADE_PP,
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) END AS RENTABILIDADE_PT,
                            CASE WHEN SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) IS NULL THEN 0 ELSE SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.ANALISE_LUCRO ELSE 0 END) END AS RENTABILIDADE_PQ

                        FROM
                            (SELECT CHAVE_NOTA, SUM(PESO_LIQUIDO) AS PESO_LIQUIDO FROM COPLAS.NOTAS_ITENS GROUP BY CHAVE_NOTA) NOTAS_PESO_LIQUIDO,
                            COPLAS.PRODUTOS,
                            COPLAS.NOTAS_ITENS,
                            COPLAS.VENDEDORES,
                            COPLAS.NOTAS,
                            COPLAS.CLIENTES

                        WHERE
                            NOTAS.CHAVE = NOTAS_PESO_LIQUIDO.CHAVE_NOTA(+) AND
                            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
                            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
                            PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
                            NOTAS.VALOR_COMERCIAL = 'SIM' AND
                            NOTAS.ESPECIE = 'E' AND
                            PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND

                            -- primeiro dia do mes
                            NOTAS.DATA_EMISSAO >= TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                            -- ultimo dia do mes
                            NOTAS.DATA_EMISSAO <= TO_DATE('{ultimo_dia_mes}','DD-MM-YYYY')
                    ) DEVOLUCOES,
                    (
                        SELECT
                            ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

                        FROM
                            (
                                SELECT
                                    VENDEDORES.NOMERED AS CARTEIRA,
                                    PEDIDOS.NUMPED,
                                    PRODUTOS.CHAVE_FAMILIA,
                                    PRODUTOS.CODIGO,
                                    ROUND(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS VALOR_MERCADORIAS,
                                    ROUND(PEDIDOS_ITENS.ANALISE_LUCRO - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS MC,
                                    ROUND(PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM), 2) AS RATEIO_FRETE,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * PEDIDOS_ITENS.ALIQUOTA_IPI / 100, 2) AS IPI,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (CASE WHEN PEDIDOS_ITENS.ANALISE_PIS = 0 THEN 0 ELSE 0.65 END * (1 - (PEDIDOS_ITENS.ICMS_ALIQUOTA * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100))) / 100, 2) AS PIS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (CASE WHEN PEDIDOS_ITENS.ANALISE_COFINS = 0 THEN 0 ELSE 3 END * (1 - (PEDIDOS_ITENS.ICMS_ALIQUOTA * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100))) / 100, 2) AS COFINS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * (PEDIDOS_ITENS.ICMS_ALIQUOTA + CASE WHEN CLIENTES.ISENTO_INSCRICAO = 'SIM' AND PEDIDOS_ITENS.DESTINO_MERCADORIAS = 'CONSUMO' THEN (SELECT ALIQUOTA_FCP FROM COPLAS.MATRIZ_ICMS WHERE UF_EMITENTE = UF_DESTINO AND UF_EMITENTE = COALESCE(PLATAFORMAS.UF_ENT, CLIENTES.UF)) ELSE 0 END + CASE WHEN PEDIDOS_ITENS.ANALISE_ICMS_PARTILHA = 0 THEN 0 ELSE (SELECT ALIQUOTA FROM COPLAS.MATRIZ_ICMS WHERE UF_EMITENTE = UF_DESTINO AND UF_EMITENTE = COALESCE(PLATAFORMAS.UF_ENT, CLIENTES.UF)) - PEDIDOS_ITENS.ICMS_ALIQUOTA END) * CASE WHEN PEDIDOS_ITENS.DESTINO_MERCADORIAS != 'CONSUMO' THEN 1 ELSE 1 + PEDIDOS_ITENS.ALIQUOTA_IPI / 100 END / 100, 2) AS ICMS,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS_ITENS.ANALISE_CONTRIBUICAO = 0 THEN 0 ELSE 2 END / 100, 2) AS IR,
                                    ROUND((PEDIDOS_ITENS.RATEIO_FRETE + (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS_ITENS.ANALISE_CONTRIBUICAO = 0 THEN 0 ELSE 1.08 END / 100, 2) AS CSLL,
                                    ROUND(CASE WHEN PEDIDOS.VALOR_FRETE_INCL_ITEM = 0 THEN 0 ELSE (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) * PEDIDOS_ITENS.COMISSAO_PADRAO_PERC / 100 END, 2) AS COMISSAO_FRETE_ITEM,
                                    ROUND(CASE WHEN PEDIDOS.VALOR_FRETE_INCL_ITEM = 0 THEN 0 ELSE (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) * PEDIDOS_ITENS.ANALISE_DESPESAS_ADM / PEDIDOS_ITENS.VALOR_TOTAL END, 2) AS DESPESA_ADM_FRETE_ITEM

                                FROM
                                    COPLAS.PLATAFORMAS,
                                    COPLAS.CLIENTES,
                                    COPLAS.VENDEDORES,
                                    COPLAS.PRODUTOS,
                                    COPLAS.PEDIDOS_ITENS,
                                    COPLAS.PEDIDOS

                                WHERE
                                    PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
                                    CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
                                    CLIENTES.CHAVE_VENDEDOR3 = VENDEDORES.CODVENDEDOR AND
                                    PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
                                    PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
                                    PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND

                                    (
                                        (
                                            -- primeiro dia do mes
                                            PEDIDOS.DATA_PEDIDO < TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                                            -- primeiro dia util do mes
                                            PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE('{primeiro_dia_util_mes}','DD-MM-YYYY') AND
                                            -- primeiro dia util do proximo mes
                                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                                        ) OR
                                        (
                                            -- primeiro dia do mes
                                            PEDIDOS.DATA_PEDIDO >= TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                                            -- ultimo dia do mes
                                            PEDIDOS.DATA_PEDIDO <= TO_DATE('{ultimo_dia_mes}','DD-MM-YYYY') AND
                                            -- primeiro dia util do proximo mes
                                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                                        )
                                    )
                            )
                    ) LFRETE,
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
                    PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND

                    (
                        (
                            -- primeiro dia do mes
                            PEDIDOS.DATA_PEDIDO < TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                            -- primeiro dia util do mes
                            PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE('{primeiro_dia_util_mes}','DD-MM-YYYY') AND
                            -- primeiro dia util do proximo mes
                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                        ) OR
                        (
                            -- primeiro dia do mes
                            PEDIDOS.DATA_PEDIDO >= TO_DATE('{primeiro_dia_mes}','DD-MM-YYYY') AND
                            -- ultimo dia do mes
                            PEDIDOS.DATA_PEDIDO <= TO_DATE('{ultimo_dia_mes}','DD-MM-YYYY') AND
                            -- primeiro dia util do proximo mes
                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE('{primeiro_dia_util_proximo_mes}','DD-MM-YYYY')
                        )
                    )

                GROUP BY
                    DEVOLUCOES.PP,
                    DEVOLUCOES.PT,
                    DEVOLUCOES.PQ,
                    DEVOLUCOES.TOTAL,
                    DEVOLUCOES.RENTABILIDADE,
                    DEVOLUCOES.RENTABILIDADE_PP,
                    DEVOLUCOES.RENTABILIDADE_PT,
                    DEVOLUCOES.RENTABILIDADE_PQ,
                    LFRETE.MC_SEM_FRETE,
                    LFRETE.MC_SEM_FRETE_PP,
                    LFRETE.MC_SEM_FRETE_PT,
                    LFRETE.MC_SEM_FRETE_PQ
            )
    """

    sql = sql.format(despesa_administrativa_fixa=despesa_administrativa_fixa, primeiro_dia_mes=primeiro_dia_mes,
                     primeiro_dia_util_mes=primeiro_dia_util_mes, ultimo_dia_mes=ultimo_dia_mes,
                     primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    resultado = executar(sql)

    mc_mes = 0.0 if not resultado[0][0] else resultado[0][0]
    total_mes_sem_converter_moeda = 0.0 if not resultado[0][1] else resultado[0][1]
    rentabilidade_mes = 0.0 if not resultado[0][2] else resultado[0][2]

    dicionario = {
        'mc_mes': float(mc_mes),
        'total_mes_sem_converter_moeda': float(total_mes_sem_converter_moeda),
        'rentabilidade_mes': float(rentabilidade_mes)
    }

    return dicionario
