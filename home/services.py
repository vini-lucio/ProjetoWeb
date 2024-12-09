from utils.oracle.conectar import executar_oracle
from utils.conectar_database_django import executar_django
from home.models import Cidades
from utils.site_setup import get_cidades, get_estados, get_site_setup


def contas_estrategicas_ano_mes_a_mes():
    """Totaliza o valor das contas estrategicas do ano informado em site setup mes a mes de janeiro até o mes informado"""
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
    """Totaliza a quantidade de funcionarios ativos do ano informado em site setup mes a mes de janeiro até o mes informado"""
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
    """Totaliza a proporção dos salarios de custo de produção com o resto, dos funcionarios ativos do ano informado em site setup mes a mes de janeiro até o mes informado"""
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
