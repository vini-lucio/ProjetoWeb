from utils.oracle.conectar import executar_oracle
from utils.conectar_database_django import executar_django
from home.models import Cidades
from utils.site_setup import get_cidades, get_estados, get_site_setup


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
