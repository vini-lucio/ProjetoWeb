from utils.oracle.conectar import executar_oracle
from utils.conectar_database_django import executar_django
from home.models import Cidades
from utils.site_setup import get_cidades, get_estados, get_site_setup


def ativo_operacional_materia_prima_ano_mes_a_mes():
    """Totaliza o ativo operacional das materias primas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            AO_MP_PP.MES,
            ROUND(AO_MP_PP.AO_MP_PP, 2) AS AO_MP_PP,
            ROUND(AO_MP_PT.AO_MP_PT, 2) AS AO_MP_PT,
            ROUND(AO_MP_PQ.AO_MP_PQ2, 2) AS AO_MP_PQ

        FROM
            (
                SELECT
                    ULTIMA_MOVIMENTACAO.MES,
                    SUM(CASE WHEN MATERIAIS.CHAVE_FAMILIA = 7766 THEN MOVESTOQUE.SALDO_ESTOQUE * CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO ELSE 0 END) AS AO_MP_PP

                FROM
                    COPLAS.CUSTOS_PRODUTOS_LOG,
                    COPLAS.MOVESTOQUE,
                    (
                        SELECT DISTINCT
                            PRODUTOS.CHAVE_FAMILIA,
                            MATERIAIS.CPROD,
                            MATERIAIS_JOBS_CUSTOS.CUSTO_TOTAL

                        FROM
                            COPLAS.PRODUTOS,
                            COPLAS.PRODUTOS MATERIAIS,
                            COPLAS.PROCESSOS,
                            COPLAS.PROCESSOS_MATERIAIS,
                            COPLAS.PRODUTOS_JOBS_CUSTOS MATERIAIS_JOBS_CUSTOS

                        WHERE
                            MATERIAIS.CPROD = MATERIAIS_JOBS_CUSTOS.CHAVE_PRODUTO AND
                            PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                            PROCESSOS_MATERIAIS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
                            PROCESSOS_MATERIAIS.CHAVE_MATERIAL = MATERIAIS.CPROD AND
                            MATERIAIS_JOBS_CUSTOS.CHAVE_JOB = 22 AND
                            PRODUTOS.CHAVE_FAMILIA = 7766 AND
                            MATERIAIS.CHAVE_FAMILIA NOT IN (7766, 7767, 8378)
                    ) MATERIAIS,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                        FROM
                            COPLAS.MOVESTOQUE,
                            (
                                SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                            ) PERIODO

                        WHERE
                            EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND
                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            MOVESTOQUE.CHAVE_PRODUTO
                    ) ULTIMA_MOVIMENTACAO,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(CUSTOS_PRODUTOS_LOG.CHAVE) AS ULTIMO_CUSTO

                        FROM
                            COPLAS.CUSTOS_PRODUTOS_LOG,
                            (
                                SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                            ) PERIODO

                        WHERE
                            CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO > 0 AND
                            CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22 AND
                            EXTRACT(YEAR FROM CUSTOS_PRODUTOS_LOG.DATA) + EXTRACT(MONTH FROM CUSTOS_PRODUTOS_LOG.DATA) / 12.00 + EXTRACT(DAY FROM CUSTOS_PRODUTOS_LOG.DATA) / 365.00 < PERIODO.ANOMESDIA AND
                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO
                    ) ULTIMO_CUSTO

                WHERE
                    ULTIMO_CUSTO.MES = ULTIMA_MOVIMENTACAO.MES AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO = MATERIAIS.CPROD AND
                    CUSTOS_PRODUTOS_LOG.CHAVE = ULTIMO_CUSTO.ULTIMO_CUSTO AND
                    ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO = MOVESTOQUE.CHAVE AND
                    MOVESTOQUE.CHAVE_PRODUTO = MATERIAIS.CPROD AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22 AND
                    MOVESTOQUE.SALDO_ESTOQUE != 0

                GROUP BY
                    ULTIMA_MOVIMENTACAO.MES

                ORDER BY
                    ULTIMA_MOVIMENTACAO.MES
            ) AO_MP_PP,
            (
                SELECT
                    ULTIMA_MOVIMENTACAO_SALDO.MES,
                    SUM(ULTIMA_MOVIMENTACAO_SALDO.SALDO_ESTOQUE * CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO) AS AO_MP_PT

                FROM
                    COPLAS.CUSTOS_PRODUTOS_LOG,
                    (
                        SELECT DISTINCT
                            MATERIAIS.CODIGO,
                            MATERIAIS.CPROD,
                            MATERIAIS_JOBS_CUSTOS.CUSTO_TOTAL

                        FROM
                            COPLAS.PRODUTOS MATERIAIS,
                            COPLAS.PRODUTOS_JOBS_CUSTOS MATERIAIS_JOBS_CUSTOS

                        WHERE
                            MATERIAIS.CPROD = MATERIAIS_JOBS_CUSTOS.CHAVE_PRODUTO AND
                            MATERIAIS_JOBS_CUSTOS.CHAVE_JOB = 22
                    ) MATERIAIS,
                    (
                        SELECT
                            PRODUTOS_PERIODO.MES,
                            PRODUTOS_PERIODO.CHAVE_PRODUTO,
                            COALESCE(ULTIMO_SALDO.SALDO_ESTOQUE, 0) AS SALDO_ESTOQUE

                        FROM
                            (
                                SELECT
                                    PERIODO.MES,
                                    PRODUTOS.CODIGO,
                                    PRODUTOS.CPROD AS CHAVE_PRODUTO

                                FROM
                                    COPLAS.PRODUTOS,
                                    (
                                        SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                        SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                                    ) PERIODO
                            ) PRODUTOS_PERIODO,
                            (
                                SELECT
                                    EXTRACT(MONTH FROM ESTOQUE_TERCEIROS_DIARIO.DATA) AS MES,
                                    ESTOQUE_TERCEIROS_DIARIO.CHAVE_PRODUTO,
                                    ESTOQUE_TERCEIROS_DIARIO.QUANTIDADE AS SALDO_ESTOQUE

                                FROM
                                    COPLAS.ESTOQUE_TERCEIROS_DIARIO

                                WHERE
                                    ESTOQUE_TERCEIROS_DIARIO.CHAVE_FORNECEDOR = 19688 AND
                                    EXTRACT(YEAR FROM ESTOQUE_TERCEIROS_DIARIO.DATA) = :ano AND
                                    ESTOQUE_TERCEIROS_DIARIO.DATA = LAST_DAY(ESTOQUE_TERCEIROS_DIARIO.DATA)
                            ) ULTIMO_SALDO

                        WHERE
                            PRODUTOS_PERIODO.CHAVE_PRODUTO = ULTIMO_SALDO.CHAVE_PRODUTO(+) AND
                            PRODUTOS_PERIODO.MES = ULTIMO_SALDO.MES(+)
                    ) ULTIMA_MOVIMENTACAO_SALDO,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(CUSTOS_PRODUTOS_LOG.CHAVE) AS ULTIMO_CUSTO

                        FROM
                            COPLAS.CUSTOS_PRODUTOS_LOG,
                            (
                                SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                            ) PERIODO

                        WHERE
                            CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO > 0 AND
                            CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22 AND
                            EXTRACT(YEAR FROM CUSTOS_PRODUTOS_LOG.DATA) + EXTRACT(MONTH FROM CUSTOS_PRODUTOS_LOG.DATA) / 12.00 + EXTRACT(DAY FROM CUSTOS_PRODUTOS_LOG.DATA) / 365.00 < PERIODO.ANOMESDIA AND
                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO
                    ) ULTIMO_CUSTO

                WHERE
                    ULTIMO_CUSTO.MES = ULTIMA_MOVIMENTACAO_SALDO.MES AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO = MATERIAIS.CPROD AND
                    CUSTOS_PRODUTOS_LOG.CHAVE = ULTIMO_CUSTO.ULTIMO_CUSTO AND
                    ULTIMA_MOVIMENTACAO_SALDO.CHAVE_PRODUTO = MATERIAIS.CPROD AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22

                GROUP BY
                    ULTIMA_MOVIMENTACAO_SALDO.MES

                ORDER BY
                    ULTIMA_MOVIMENTACAO_SALDO.MES
            ) AO_MP_PT,
            (
                SELECT
                    ULTIMA_MOVIMENTACAO.MES,
                    SUM(O3.MOVESTOQUE.SALDO_ESTOQUE * MATERIAIS.CUSTO_TOTAL) AS AO_MP_PQ,
                    SUM(O3.MOVESTOQUE.SALDO_ESTOQUE * CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO) AS AO_MP_PQ2

                FROM
                    COPLAS.CUSTOS_PRODUTOS_LOG,
                    O3.PRODUTOS,
                    O3.MOVESTOQUE,
                    (
                        SELECT DISTINCT
                            MATERIAIS.CPROD,
                            MATERIAIS.CODIGO,
                            MATERIAIS_JOBS_CUSTOS.CUSTO_TOTAL

                        FROM
                            COPLAS.PRODUTOS,
                            COPLAS.PRODUTOS MATERIAIS,
                            COPLAS.PROCESSOS,
                            COPLAS.PROCESSOS_MATERIAIS,
                            COPLAS.PRODUTOS_JOBS_CUSTOS MATERIAIS_JOBS_CUSTOS

                        WHERE
                            MATERIAIS.CPROD = MATERIAIS_JOBS_CUSTOS.CHAVE_PRODUTO AND
                            PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                            PROCESSOS_MATERIAIS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
                            PROCESSOS_MATERIAIS.CHAVE_MATERIAL = MATERIAIS.CPROD AND
                            MATERIAIS_JOBS_CUSTOS.CHAVE_JOB = 22 AND
                            PRODUTOS.CHAVE_FAMILIA IN (8378) AND
                            MATERIAIS.CHAVE_FAMILIA NOT IN (7766, 7767, 8378)
                    ) MATERIAIS,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(O3.MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                        FROM
                            O3.MOVESTOQUE,
                            (
                                SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                            ) PERIODO

                        WHERE
                            EXTRACT(YEAR FROM O3.MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM O3.MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM O3.MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND
                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            O3.MOVESTOQUE.CHAVE_PRODUTO
                    ) ULTIMA_MOVIMENTACAO,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(CUSTOS_PRODUTOS_LOG.CHAVE) AS ULTIMO_CUSTO

                        FROM
                            COPLAS.CUSTOS_PRODUTOS_LOG,
                            (
                                SELECT 12 AS MES, :ano + (12 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 11 AS MES, :ano + (11 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 10 AS MES, :ano + (10 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 9 AS MES, :ano + (9 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 8 AS MES, :ano + (8 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 7 AS MES, :ano + (7 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 6 AS MES, :ano + (6 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 5 AS MES, :ano + (5 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 4 AS MES, :ano + (4 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 3 AS MES, :ano + (3 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 2 AS MES, :ano + (2 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL UNION ALL
                                SELECT 1 AS MES, :ano + (1 + 1) / 12.00 + 1 / 365.00 AS ANOMESDIA FROM DUAL
                            ) PERIODO

                        WHERE
                            CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO > 0 AND
                            CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22 AND
                            EXTRACT(YEAR FROM CUSTOS_PRODUTOS_LOG.DATA) + EXTRACT(MONTH FROM CUSTOS_PRODUTOS_LOG.DATA) / 12.00 + EXTRACT(DAY FROM CUSTOS_PRODUTOS_LOG.DATA) / 365.00 < PERIODO.ANOMESDIA AND
                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO
                    ) ULTIMO_CUSTO

                WHERE
                    ULTIMO_CUSTO.MES = ULTIMA_MOVIMENTACAO.MES AND
                    ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO = O3.MOVESTOQUE.CHAVE AND
                    O3.MOVESTOQUE.CHAVE_PRODUTO = O3.PRODUTOS.CPROD AND
                    O3.PRODUTOS.CODIGO = MATERIAIS.CODIGO AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO = MATERIAIS.CPROD AND
                    CUSTOS_PRODUTOS_LOG.CHAVE = ULTIMO_CUSTO.ULTIMO_CUSTO AND
                    CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22 AND
                    O3.MOVESTOQUE.SALDO_ESTOQUE != 0

                GROUP BY
                    ULTIMA_MOVIMENTACAO.MES

                ORDER BY
                    ULTIMA_MOVIMENTACAO.MES
            ) AO_MP_PQ

        WHERE
            AO_MP_PP.MES = AO_MP_PQ.MES(+) AND
            AO_MP_PP.MES = AO_MP_PT.MES(+)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    if not resultado:
        return []

    return resultado


def horas_produtivas_ano_mes_a_mes():
    """Totaliza a quantidade de horas produtivas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO) AS MES,
            ROUND(SUM(APONTAMENTOS.TEMPO) / 60, 2) AS HORAS

        FROM
            COPLAS.APONTAMENTOS

        WHERE
            APONTAMENTOS.CHAVE_SETOR=3 AND

            -- primeiro dia do ano
            TRUNC(APONTAMENTOS.INICIO) >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
            -- ultimo dia do ano
            TRUNC(APONTAMENTOS.INICIO) <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)

        ORDER BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    if not resultado:
        return []

    return resultado


def frete_cif_ano_mes_a_mes():
    """Totaliza o valor dos fretes CIF do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM PAGAR.DATAEMISSAO) AS MES,
            ROUND(SUM(CASE WHEN FORNECEDORES.NOMERED LIKE '%AGILLI BRASIL%' AND PAGAR.STATUS != 'PREVISAO' THEN PAGAR.VALORTOTAL * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS AGILLI,
            ROUND(SUM(CASE WHEN FORNECEDORES.NOMERED NOT LIKE '%AGILLI BRASIL%' THEN PAGAR.VALORTOTAL * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS OUTRAS_TRANSPORTADORAS

        FROM
            COPLAS.FORNECEDORES,
            COPLAS.PAGAR,
            COPLAS.PAGAR_PLANOCONTA,
            COPLAS.PAGAR_CENTRORESULTADO,
            COPLAS.PAGAR_JOB,
            COPLAS.PLANO_DE_CONTAS

        WHERE
            PAGAR.CODFOR = FORNECEDORES.CODFOR AND
            PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
            PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
            PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
            PAGAR_JOB.CHAVE_JOB IN (22, 24) AND
            PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS IN (1377, 1580, 1613, 1614, 1616, 1617, 1618) AND

            -- primeiro dia do ano
            PAGAR.DATAEMISSAO >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
            -- ultimo dia do ano
            PAGAR.DATAEMISSAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM PAGAR.DATAEMISSAO)

        ORDER BY
            EXTRACT(MONTH FROM PAGAR.DATAEMISSAO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    if not resultado:
        return []

    return resultado


def financeiro_ano_mes_a_mes():
    """Totaliza o valor das grandes contas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            MES,
            SUM(FINANCEIRO.RECEITAS) AS RECEITAS,
            SUM(FINANCEIRO.CUSTOS_VARIAVEIS) AS CUSTOS_VARIAVEIS,
            SUM(FINANCEIRO.CUSTOS_FIXOS) AS CUSTOS_FIXOS,
            SUM(FINANCEIRO.INVESTIMENTOS) AS INVESTIMENTOS

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS RECEITAS,
                    0 AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS CUSTOS_VARIAVEIS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS INVESTIMENTOS

                FROM
                    COPLAS.PAGAR,
                    COPLAS.PAGAR_PLANOCONTA,
                    COPLAS.PAGAR_CENTRORESULTADO,
                    COPLAS.PAGAR_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
                    PAGAR_JOB.CHAVE_JOB IN (22, 24) AND
                    PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND

                    -- primeiro dia do ano
                    PAGAR.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS RECEITAS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS CUSTOS_VARIAVEIS,
                    0 AS CUSTOS_VARIAVEIS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS CUSTOS_FIXOS,
                    0 AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS INVESTIMENTOS

                FROM
                    COPLAS.RECEBER,
                    COPLAS.RECEBER_PLANOCONTA,
                    COPLAS.RECEBER_CENTRORESULTADO,
                    COPLAS.RECEBER_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    RECEBER_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    RECEBER.CHAVE = RECEBER_PLANOCONTA.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_CENTRORESULTADO.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND
                    RECEBER_JOB.CHAVE_JOB IN (22, 24) AND
                    RECEBER_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND

                    -- primeiro dia do ano
                    RECEBER.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    RECEBER.DATALIQUIDACAO <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM MOVBAN.DATA) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS CUSTOS_VARIAVEIS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS INVESTIMENTOS

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN.AUTOMATICO = 'NAO' AND
                    MOVBAN_JOB.CHAVE_JOB IN (22, 24) AND
                    MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND

                    -- primeiro dia do ano
                    MOVBAN.DATA >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    MOVBAN.DATA <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM MOVBAN.DATA)
            ) FINANCEIRO
        GROUP BY
            MES

        ORDER BY
            MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    if not resultado:
        return []

    return resultado


def financeiro_geral_ano_mes_a_mes():
    """Totaliza o valor geral das grandes contas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            MES,
            SUM(RECEITAS) AS RECEITAS,
            SUM(CUSTOS_VARIAVEIS) AS CUSTOS_VARIAVEIS,
            SUM(CUSTOS_FIXOS) AS CUSTOS_FIXOS,
            SUM(INVESTIMENTOS) AS INVESTIMENTOS

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS RECEITAS,
                    0 AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS CUSTOS_VARIAVEIS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS INVESTIMENTOS

                FROM
                    COPLAS.PAGAR,
                    COPLAS.PAGAR_PLANOCONTA,
                    COPLAS.PAGAR_CENTRORESULTADO,
                    COPLAS.PAGAR_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND

                    -- primeiro dia do ano
                    PAGAR.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS RECEITAS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS CUSTOS_VARIAVEIS,
                    0 AS CUSTOS_VARIAVEIS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS CUSTOS_FIXOS,
                    0 AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS INVESTIMENTOS

                FROM
                    COPLAS.RECEBER,
                    COPLAS.RECEBER_PLANOCONTA,
                    COPLAS.RECEBER_CENTRORESULTADO,
                    COPLAS.RECEBER_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    RECEBER_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    RECEBER.CHAVE = RECEBER_PLANOCONTA.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_CENTRORESULTADO.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND

                    -- primeiro dia do ano
                    RECEBER.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    RECEBER.DATALIQUIDACAO <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM MOVBAN.DATA) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS CUSTOS_VARIAVEIS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS CUSTOS_FIXOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '4.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS INVESTIMENTOS

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN.AUTOMATICO = 'NAO' AND

                    -- primeiro dia do ano
                    MOVBAN.DATA >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do ano
                    MOVBAN.DATA <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM MOVBAN.DATA)
            ) FINANCEIRO

        GROUP BY
            MES

        ORDER BY
            MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    if not resultado:
        return []

    return resultado


def receitas_despesas_ano_mes_a_mes_12_meses():
    """Totaliza as receitas e despesas do periodo informado em site setup mes a mes (ultimos 12 meses de cada mes)"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            ADM.MES,
            ROUND(SUM(ADM.RECEITAS), 2) AS RECEITAS,
            ROUND(SUM(ADM.SUBTRAIR_S), 2) AS SUBTRAIR_S,
            ROUND(SUM(ADM.SUBTRAIR_M), 2) AS SUBTRAIR_M,
            ROUND(SUM(ADM.PIS_COFINS_CSLL_IRPJ), 2) AS PIS_COFINS_CSLL_IRPJ,
            ROUND(SUM(ADM.ICMS), 2) AS ICMS,
            ROUND(SUM(ADM.COMISSOES), 2) AS COMISSOES,
            ROUND(SUM(ADM.ADM), 2) AS ADM,
            ROUND(SUM(ADM.CP), 2) AS CP,
            ROUND(SUM(ADM.ADM_CP), 2) AS ADM_CP,
            ROUND(SUM(ADM.ADMV), 2) AS ADMV,
            ROUND(SUM(ADM.ADMF), 2) AS ADMF,
            ROUND(SUM(ADM.TOTAL_VARIAVEL), 2) AS TOTAL_VARIAVEL,
            ROUND(SUM(ADM.TOTAL_FIXO), 2) AS TOTAL_FIXO

        FROM
            (
                SELECT
                    PERIODO.MES,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS RECEITAS,
                    0 AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS TOTAL_VARIAVEL,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS TOTAL_FIXO,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%-SUBTRAIR%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS SUBTRAIR_S,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%*SUBTRAIR%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS SUBTRAIR_M,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKPCIC%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS PIS_COFINS_CSLL_IRPJ,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKICMS%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS ICMS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKCOM%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS COMISSOES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) * (-1) AS ADM,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) * (-1) AS ADMV,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) * (-1) AS ADMF,
                    (ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) - ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP-O3%' AND PAGAR_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2)) * (-1) AS CP,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS ADM_CP

                FROM
                    COPLAS.PAGAR,
                    COPLAS.PAGAR_PLANOCONTA,
                    COPLAS.PAGAR_CENTRORESULTADO,
                    COPLAS.PAGAR_JOB,
                    COPLAS.PLANO_DE_CONTAS,
                    (
                        SELECT 12 AS MES, :ano + 12 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 11 AS MES, :ano + 11 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 10 AS MES, :ano + 10 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 9 AS MES, :ano + 9 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 8 AS MES, :ano + 8 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 7 AS MES, :ano + 7 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 6 AS MES, :ano + 6 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 5 AS MES, :ano + 5 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 4 AS MES, :ano + 4 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 3 AS MES, :ano + 3 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 2 AS MES, :ano + 2 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 1 AS MES, :ano + 1 / 12.00 AS ANOMES FROM DUAL
                    ) PERIODO

                WHERE
                    PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
                    PAGAR_JOB.CHAVE_JOB IN (22, 24) AND
                    PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '4.%' AND
                    EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) + EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) / 12 >= PERIODO.ANOMES - 11 / 12 AND
                    EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) + EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) / 12 <= PERIODO.ANOMES AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES

                UNION ALL

                SELECT
                    PERIODO.MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS RECEITAS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS TOTAL_VARIAVEL,
                    0 AS TOTAL_VARIAVEL,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS TOTAL_FIXO,
                    0 AS TOTAL_FIXO,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%-SUBTRAIR%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SUBTRAIR_S,
                    0 AS SUBTRAIR_S,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%*SUBTRAIR%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SUBTRAIR_M,
                    0 AS SUBTRAIR_M,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKPCIC%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS PIS_COFINS_CSLL_IRPJ,
                    0 AS PIS_COFINS_CSLL_IRPJ,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKICMS%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS ICMS,
                    0 AS ICMS,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKCOM%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS COMISSOES,
                    0 AS COMISSOES,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS ADM,
                    0 AS ADM,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS ADMV,
                    0 AS ADMV,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS ADMF,
                    0 AS ADMF,
                    -- (ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2)-ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP-O3%' AND RECEBER_CENTRORESULTADO.CHAVE_CENTRO=47 THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2)) AS CP,
                    0 AS CP,
                    -- ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS ADM_CP
                    0 AS ADM_CP

                FROM
                    COPLAS.RECEBER,
                    COPLAS.RECEBER_PLANOCONTA,
                    COPLAS.RECEBER_CENTRORESULTADO,
                    COPLAS.RECEBER_JOB,
                    COPLAS.PLANO_DE_CONTAS,
                    (
                        SELECT 12 AS MES, :ano + 12 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 11 AS MES, :ano + 11 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 10 AS MES, :ano + 10 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 9 AS MES, :ano + 9 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 8 AS MES, :ano + 8 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 7 AS MES, :ano + 7 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 6 AS MES, :ano + 6 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 5 AS MES, :ano + 5 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 4 AS MES, :ano + 4 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 3 AS MES, :ano + 3 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 2 AS MES, :ano + 2 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 1 AS MES, :ano + 1 / 12.00 AS ANOMES FROM DUAL
                    ) PERIODO

                WHERE
                    RECEBER_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    RECEBER.CHAVE = RECEBER_PLANOCONTA.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_CENTRORESULTADO.CHAVE_RECEBER AND
                    RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND
                    RECEBER_JOB.CHAVE_JOB IN (22, 24) AND
                    RECEBER_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '4.%' AND
                    EXTRACT(YEAR FROM RECEBER.DATALIQUIDACAO) + EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO) / 12 >= PERIODO.ANOMES - 11 / 12 AND
                    EXTRACT(YEAR FROM RECEBER.DATALIQUIDACAO) + EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO) / 12 <= PERIODO.ANOMES AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES

                UNION ALL

                SELECT
                    PERIODO.MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '1.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS RECEITAS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS TOTAL_VARIAVEL,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS TOTAL_FIXO,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%-SUBTRAIR%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS SUBTRAIR_S,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%*SUBTRAIR%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS SUBTRAIR_M,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKPCIC%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS PIS_COFINS_CSLL_IRPJ,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKICMS%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS ICMS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKCOM%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS COMISSOES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END END ELSE 0 END), 2) AS ADM,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '2.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END END ELSE 0 END), 2) AS ADMV,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM%' AND PLANO_DE_CONTAS.CONTA LIKE '3.%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END END ELSE 0 END), 2) AS ADMF,
                    (ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP%' THEN CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN 0 ELSE CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END END ELSE 0 END), 2) - ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%CP-O3%' AND MOVBAN_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2)) AS CP,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.DESCRICAO LIKE '%MKADM/CP%' THEN CASE WHEN MOVBAN.TIPO = 'D' THEN (MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) * (-1) ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END ELSE 0 END), 2) AS ADM_CP

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.PLANO_DE_CONTAS,
                    (
                        SELECT 12 AS MES, :ano + 12 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 11 AS MES, :ano + 11 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 10 AS MES, :ano + 10 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 9 AS MES, :ano + 9 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 8 AS MES, :ano + 8 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 7 AS MES, :ano + 7 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 6 AS MES, :ano + 6 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 5 AS MES, :ano + 5 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 4 AS MES, :ano + 4 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 3 AS MES, :ano + 3 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 2 AS MES, :ano + 2 / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 1 AS MES, :ano + 1 / 12.00 AS ANOMES FROM DUAL
                    ) PERIODO

                WHERE
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN.AUTOMATICO = 'NAO' AND
                    MOVBAN_JOB.CHAVE_JOB IN (22, 24) AND
                    MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '4.%' AND
                    EXTRACT(YEAR FROM MOVBAN.DATA) + EXTRACT(MONTH FROM MOVBAN.DATA) / 12 >= PERIODO.ANOMES - 11 / 12 AND
                    EXTRACT(YEAR FROM MOVBAN.DATA) + EXTRACT(MONTH FROM MOVBAN.DATA) / 12 <= PERIODO.ANOMES AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES
            ) ADM

        GROUP BY
            ADM.MES

        ORDER BY
            ADM.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    if not resultado:
        return []

    return resultado


def minutos_produtivos_ano_mes_a_mes_12_meses():
    """Totaliza os minutos produtivos do periodo informado em site setup mes a mes (ultimos 12 meses de cada mes)"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            PERIODO.MES,
            SUM(TEMPO) AS MINUTOS

        FROM
            COPLAS.APONTAMENTOS,
            (
                SELECT 12 AS MES, :ano + 12 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 11 AS MES, :ano + 11 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 10 AS MES, :ano + 10 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 9 AS MES, :ano + 9 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 8 AS MES, :ano + 8 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 7 AS MES, :ano + 7 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 6 AS MES, :ano + 6 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 5 AS MES, :ano + 5 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 4 AS MES, :ano + 4 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 3 AS MES, :ano + 3 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 2 AS MES, :ano + 2 / 12.00 AS ANOMES FROM DUAL UNION ALL
                SELECT 1 AS MES, :ano + 1 / 12.00 AS ANOMES FROM DUAL
            ) PERIODO

        WHERE
            APONTAMENTOS.CHAVE_SETOR = 3 AND
            EXTRACT(YEAR FROM APONTAMENTOS.INICIO) + EXTRACT(MONTH FROM APONTAMENTOS.INICIO) / 12.00 >= PERIODO.ANOMES - 11 / 12 AND
            EXTRACT(YEAR FROM APONTAMENTOS.INICIO) + EXTRACT(MONTH FROM APONTAMENTOS.INICIO) / 12.00 <= PERIODO.ANOMES AND

            PERIODO.MES <= :mes

        GROUP BY
            PERIODO.MES

        ORDER BY
            PERIODO.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    if not resultado:
        return []

    return resultado


def contas_estrategicas_ano_mes_a_mes():
    """Totaliza o valor das contas estrategicas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            CONTAS_ESTRATEGICAS.MES,
            SUM(CONTAS_ESTRATEGICAS.MERCADORIA_REVENDA) AS MERCADORIA_REVENDA,
            SUM(CONTAS_ESTRATEGICAS.IMPOSTOS) AS IMPOSTOS,
            SUM(CONTAS_ESTRATEGICAS.MP) AS MP,
            SUM(CONTAS_ESTRATEGICAS.ENERGIA) AS ENERGIA,
            SUM(CONTAS_ESTRATEGICAS.SALARIOS_ENCARGOS) AS SALARIOS_ENCARGOS

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.01.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS MERCADORIA_REVENDA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.03.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS IMPOSTOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.02.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS MP,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.02.03.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS ENERGIA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.03.%' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SALARIOS_ENCARGOS

                FROM
                    COPLAS.PAGAR,
                    COPLAS.PAGAR_PLANOCONTA,
                    COPLAS.PAGAR_CENTRORESULTADO,
                    COPLAS.PAGAR_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
                    PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
                    PAGAR_JOB.CHAVE_JOB IN (22, 24) AND
                    PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    (
                        PLANO_DE_CONTAS.CONTA LIKE '2.01.01.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '2.03.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '2.01.02.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.02.03.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.03.%'
                    ) AND

                    -- primeiro dia do ano
                    PAGAR.DATALIQUIDACAO>=TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    PAGAR.DATALIQUIDACAO<=TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM MOVBAN.DATA) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.01.%' THEN MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS MERCADORIA_REVENDA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.03.%' THEN MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS IMPOSTOS,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.02.%' THEN MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS MP,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.02.03.%' THEN MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS ENERGIA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '3.03.%' THEN MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SALARIOS_ENCARGOS

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN.TIPO = 'D' AND
                    MOVBAN.AUTOMATICO = 'NAO' AND
                    MOVBAN_JOB.CHAVE_JOB IN (22, 24) AND
                    MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    (
                        PLANO_DE_CONTAS.CONTA LIKE '2.01.01.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '2.03.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '2.01.02.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.02.03.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.03.%'
                    ) AND

                    -- primeiro dia do ano
                    MOVBAN.DATA>=TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    MOVBAN.DATA<=TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM MOVBAN.DATA)
            ) CONTAS_ESTRATEGICAS

        GROUP BY
            MES

        ORDER BY
            MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    if not resultado:
        return []

    return resultado


def totalizar_funcionarios_ano_mes_a_mes():
    """Totaliza a quantidade de funcionarios ativos do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            periodo.mes,
            COUNT(rh_funcionarios.id) AS total_funcionarios

        FROM
            rh_funcionarios,
            (
                SELECT 12 AS mes, %(ano)s + 12 / 12.00 AS anomes UNION ALL
                SELECT 11 AS mes, %(ano)s + 11 / 12.00 AS anomes UNION ALL
                SELECT 10 AS mes, %(ano)s + 10 / 12.00 AS anomes UNION ALL
                SELECT 9 AS mes, %(ano)s + 9 / 12.00 AS anomes UNION ALL
                SELECT 8 AS mes, %(ano)s + 8 / 12.00 AS anomes UNION ALL
                SELECT 7 AS mes, %(ano)s + 7 / 12.00 AS anomes UNION ALL
                SELECT 6 AS mes, %(ano)s + 6 / 12.00 AS anomes UNION ALL
                SELECT 5 AS mes, %(ano)s + 5 / 12.00 AS anomes UNION ALL
                SELECT 4 AS mes, %(ano)s + 4 / 12.00 AS anomes UNION ALL
                SELECT 3 AS mes, %(ano)s + 3 / 12.00 AS anomes UNION ALL
                SELECT 2 AS mes, %(ano)s + 2 / 12.00 AS anomes UNION ALL
                SELECT 1 AS mes, %(ano)s + 1 / 12.00 AS anomes
            ) periodo

        WHERE
            rh_funcionarios.job_id IN (SELECT id FROM home_jobs WHERE descricao = 'COPLAS') AND
            EXTRACT(YEAR FROM rh_funcionarios.data_entrada) + EXTRACT(MONTH FROM rh_funcionarios.data_entrada) / 12.00 <= periodo.anomes AND
            (
                rh_funcionarios.data_saida IS NULL OR
                EXTRACT(YEAR FROM rh_funcionarios.data_saida) + EXTRACT(MONTH FROM rh_funcionarios.data_saida) / 12.00 > periodo.anomes
            ) AND

            periodo.mes <= %(mes)s

        GROUP BY
            periodo.mes

        ORDER BY
            periodo.mes
    """

    resultado = executar_django(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    if not resultado:
        return []

    return resultado


def rateio_salario_adm_cp_ano_mes_a_mes():
    """Totaliza a proporção dos salarios de custo de produção com o resto, dos funcionarios ativos do periodo informado
    em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT * FROM rateio_salario_adm_cp_ano_mes_a_mes (%(ano)s, %(mes)s)
    """

    resultado = executar_django(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    if not resultado:
        return []

    return resultado


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

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    if not resultado:
        return []

    return resultado


def get_cidades_base() -> list | None:
    """Retorna tabela de cidades atualizada"""
    sql = """
        SELECT
            CHAVE AS CHAVE_ANALYSIS,
            UF AS SIGLA,
            CIDADE AS NOME

        FROM
            COPLAS.FAIXAS_CEP
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    if not resultado:
        return []

    return resultado


def migrar_cidades():
    """Atualiza cadastro de cidades de acordo com Analysis"""
    cidades_base = get_cidades_base()
    if cidades_base:
        cidades = get_cidades()
        estados = get_estados()
        for cidade_base in cidades_base:
            cidade_conferir = cidades.filter(chave_analysis=cidade_base['CHAVE_ANALYSIS']).first()

            if not cidade_conferir or \
                    cidade_conferir.nome != cidade_base['NOME'] or \
                    cidade_conferir.estado.sigla != cidade_base['SIGLA']:

                estados_fk = estados.filter(sigla=cidade_base['SIGLA']).first()
                instancia, criado = Cidades.objects.update_or_create(
                    chave_analysis=cidade_base['CHAVE_ANALYSIS'],
                    defaults={
                        'chave_analysis': cidade_base['CHAVE_ANALYSIS'],
                        'estado': estados_fk,
                        'nome': cidade_base['NOME'],
                    }
                )
                instancia.full_clean()
                instancia.save()
