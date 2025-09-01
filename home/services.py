from typing import Iterable
from collections import Counter
from decimal import Decimal
from utils.oracle.conectar import executar_oracle
from utils.conectar_database_django import executar_django
from dashboards.services_financeiro import get_relatorios_financeiros
from home.models import (Cidades, Unidades, Produtos, Estados, EstadosIcms, Vendedores, CanaisVendas, Regioes,
                         ProdutosModelos)
from rh.models import Comissoes, ComissoesVendedores, Faturamentos, FaturamentosVendedores
from analysis.models import VENDEDORES, ESTADOS, MATRIZ_ICMS, FAIXAS_CEP, UNIDADES, PRODUTOS, CANAIS_VENDA, REGIOES
from utils.completar import completar_meses
from utils.site_setup import get_site_setup
from utils.conferir_alteracao import campo_migrar_mudou
from dateutil.relativedelta import relativedelta
import datetime
import pandas as pd


def status_orcamentos_ano_mes_a_mes():
    """Totaliza o valor dos orçamentos por status no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_ano_fim

        data_ano_inicio_anterior = data_ano_inicio - relativedelta(years=1)
        data_ano_fim_anterior = data_ano_fim - relativedelta(years=1)

    atual = get_relatorios_vendas('orcamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_mes_a_mes=True,
                                  coluna_status_produto_orcamento=True, desconsiderar_justificativas=True,
                                  considerar_itens_excluidos=True,)

    anterior = get_relatorios_vendas('orcamentos', inicio=data_ano_inicio_anterior, fim=data_ano_fim_anterior,
                                     coluna_status_produto_orcamento=True, desconsiderar_justificativas=True,
                                     considerar_itens_excluidos=True,)

    atual = pd.DataFrame(atual)
    atual = atual.rename(columns={'VALOR_MERCADORIAS': 'TOTAL_ATUAL'})

    anterior = pd.DataFrame(anterior)
    anterior = anterior.rename(columns={'VALOR_MERCADORIAS': 'TOTAL_ANTERIOR'})

    resultado = pd.merge(anterior, atual, how='outer', on='STATUS').fillna(0)
    resultado = resultado.to_dict(orient='records')

    return resultado


def tipo_clientes_ano_mes_a_mes():
    """Totaliza o valor por tipo de cliente no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_ano_fim

        data_ano_inicio_anterior = data_ano_inicio - relativedelta(years=1)
        data_ano_fim_anterior = data_ano_fim - relativedelta(years=1)

    atual = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_mes_a_mes=True,
                                  coluna_tipo_cliente=True)

    anterior = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio_anterior, fim=data_ano_fim_anterior,
                                     coluna_tipo_cliente=True)

    atual = pd.DataFrame(atual)
    atual = atual.rename(columns={'VALOR_MERCADORIAS': 'TOTAL_ATUAL'})

    anterior = pd.DataFrame(anterior)
    anterior = anterior.rename(columns={'VALOR_MERCADORIAS': 'TOTAL_ANTERIOR'})

    resultado = pd.merge(anterior, atual, how='outer', on='TIPO_CLIENTE').fillna(0)
    resultado = resultado.to_dict(orient='records')

    return resultado


def contas_marketing_ano_mes_a_mes():
    """Totaliza o valor das contas de marketing no periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    relatorios = []
    plano_contas = [
        (1396, 'CORREIOS'),
        (1481, 'MIDIA'),
        (1482, 'FEIRAS_EVENTOS'),
        (1483, 'BRINDES'),
        (1484, 'IMPRESSO'),
        (1537, 'INSTITUCIONAL'),
        (1561, 'PATROCINIO'),
        (1565, 'FERRAMENTAS'),
        (1608, 'CAMPANHA_COMERCIAL'),
    ]

    for chave_plano, descricao_plano in plano_contas:
        relatorio = get_relatorios_financeiros('pagar', coluna_mes_liquidacao=True, job=22,
                                               data_liquidacao_inicio=data_ano_inicio,
                                               data_liquidacao_fim=data_ano_fim, plano_conta=chave_plano)
        relatorio = completar_meses(pd.DataFrame(relatorio), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in relatorio.columns:  # type:ignore
            relatorio['VALOR_EFETIVO'] = 0  # type:ignore
        relatorio = relatorio.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        relatorios.append(relatorio)

    resultado = pd.DataFrame()
    for relatorio in relatorios:
        if resultado.empty:
            resultado = pd.DataFrame(relatorio)
            continue
        resultado = pd.merge(resultado, relatorio, how='inner', on='MES_LIQUIDACAO')

    resultado = resultado.to_dict(orient='records')

    return resultado


# TODO: trocar para get_relatorios_financeiros
def i4ref_terceirizacao_ano_mes_a_mes():
    """Totaliza o valor da terceirização do 4REF do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        ano_inicio = site_setup.atualizacoes_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
            EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) AS ANO,
            PLANO_DE_CONTAS.CONTA,
            ROUND(SUM(CASE WHEN PAGAR.CODFOR = 19476 THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS O3,
            ROUND(SUM(CASE WHEN PAGAR.CODFOR NOT IN (19476, 21542) THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS NC4,
            ROUND(SUM(CASE WHEN PAGAR.CODFOR = 21542 THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) * (-1) AS FLUXUS

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
            PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
            PAGAR_JOB.CHAVE_JOB = 22 AND
            PLANO_DE_CONTAS.CONTA LIKE '2.01.03.%' AND

            EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) >= :ano_inicio AND
            PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO),
            EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO),
            PLANO_DE_CONTAS.CONTA

        ORDER BY
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO),
            EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO),
            PLANO_DE_CONTAS.CONTA
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano_inicio=ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def i4ref_imposto_vendido_ano_mes_a_mes():
    """Totaliza o valor do imposto vendido do 4REF do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        ano_inicio = site_setup.atualizacoes_ano_inicio
        data_ano_inicio = datetime.datetime(ano_inicio, 1, 1)

        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                                      coluna_mes_emissao=True, coluna_ipi=True, coluna_st=True, coluna_icms=True,
                                      coluna_pis=True, coluna_cofins=True, coluna_irpj_csll=True,
                                      coluna_icms_partilha=True, job=22)

    resultado = pd.DataFrame(resultado)
    resultado = resultado[['MES_EMISSAO', 'ANO_EMISSAO', 'IPI', 'ST', 'ICMS', 'PIS', 'COFINS', 'IRPJ_CSLL',
                           'ICMS_PARTILHA',]]
    resultado = resultado.to_dict(orient='records')

    return resultado


def i4ref_faturado_bruto_ano_mes_a_mes():
    """Totaliza o valor do faturamento bruto do 4REF do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        ano_inicio = site_setup.atualizacoes_ano_inicio
        data_ano_inicio = datetime.datetime(ano_inicio, 1, 1)

        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                                      coluna_mes_emissao=True, coluna_valor_bruto=True, job=22)

    resultado = pd.DataFrame(resultado)
    resultado = resultado[['MES_EMISSAO', 'ANO_EMISSAO', 'VALOR_BRUTO',]]
    resultado = resultado.to_dict(orient='records')

    return resultado


def i4ref_custo_materia_prima_vendido_ano_mes_a_mes():
    """Totaliza o valor do custo das materias primas vendidas do 4REF do periodo informado em site setup mes a mes"""

    # Não funciona com a fluxus

    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        ano_inicio = site_setup.atualizacoes_ano_inicio
        data_ano_inicio = datetime.datetime(ano_inicio, 1, 1)

        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7766,
                               job=22,)
    pp = pd.DataFrame(pp)
    pp = pp[['MES_EMISSAO', 'ANO_EMISSAO', 'CUSTO_MP']]
    pp = pp.rename(columns={'CUSTO_MP': 'CUSTO_MP_PP'})

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7767,
                               job=22,)
    pt = pd.DataFrame(pt)
    pt = pt[['MES_EMISSAO', 'ANO_EMISSAO', 'CUSTO_MP']]
    pt = pt.rename(columns={'CUSTO_MP': 'CUSTO_MP_PT'})

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=8378,
                               job=22,)
    pq = pd.DataFrame(pq)
    pq = pq[['MES_EMISSAO', 'ANO_EMISSAO', 'CUSTO_MP']]
    pq = pq.rename(columns={'CUSTO_MP': 'CUSTO_MP_PQ'})

    nc4 = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim, coluna_ano_emissao=True,
                                coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7767,
                                job=22, produto_marca=181)
    nc4 = pd.DataFrame(nc4)
    nc4 = nc4[['MES_EMISSAO', 'ANO_EMISSAO', 'CUSTO_MP']]
    nc4 = nc4.rename(columns={'CUSTO_MP': 'CUSTO_MP_NC4'})

    resultado = pd.merge(pp, pt, how='outer', on=['ANO_EMISSAO', 'MES_EMISSAO'])
    resultado = pd.merge(resultado, pq, how='outer', on=['ANO_EMISSAO', 'MES_EMISSAO'])
    resultado = pd.merge(resultado, nc4, how='outer', on=['ANO_EMISSAO', 'MES_EMISSAO'])
    resultado['CUSTO_MP_SEM_NC4'] = resultado['CUSTO_MP_PT'] - resultado['CUSTO_MP_NC4']
    resultado = resultado.to_dict(orient='records')

    return resultado


# TODO: trocar para get_relatorios_financeiros
def i4ref_ano_mes_a_mes():
    """Totaliza o valor das contas do 4REF do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        ano_inicio = site_setup.atualizacoes_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            REF4.MES,
            REF4.ANO,
            REF4.CONTA,
            SUM(REF4.REF4) * (-1) AS REF4

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
                    EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) AS ANO,
                    PLANO_DE_CONTAS.CONTA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' AND PAGAR_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END), 2) AS REF4

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
                    PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    PAGAR_JOB.CHAVE_JOB = 22 AND

                    EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) >= :ano_inicio AND
                    PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO),
                    EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO),
                    PLANO_DE_CONTAS.CONTA

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM MOVBAN.DATA) AS MES,
                    EXTRACT(YEAR FROM MOVBAN.DATA) AS ANO,
                    PLANO_DE_CONTAS.CONTA,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' AND MOVBAN_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN 0 ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END * CASE WHEN MOVBAN.TIPO = 'D' THEN 1 ELSE (-1) END), 2) AS REF4

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
                    MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    MOVBAN_JOB.CHAVE_JOB = 22 AND

                    EXTRACT(YEAR FROM MOVBAN.DATA) >= :ano_inicio AND
                    MOVBAN.DATA <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM MOVBAN.DATA),
                    EXTRACT(YEAR FROM MOVBAN.DATA),
                    PLANO_DE_CONTAS.CONTA
            ) REF4

        GROUP BY
            REF4.MES,
            REF4.ANO,
            REF4.CONTA

        ORDER BY
            REF4.MES,
            REF4.ANO,
            REF4.CONTA
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano_inicio=ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def exportacoes_ano_mes_a_mes():
    """Totaliza o valor de exportações no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, carteira=738)
    resultado = completar_meses(pd.DataFrame(resultado), 'MES_EMISSAO', to_dict=True)

    return resultado


def revendas_ano_mes_a_mes():
    """Totaliza o valor de revendas no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, tipo_cliente=7552)
    resultado = completar_meses(pd.DataFrame(resultado), 'MES_EMISSAO', to_dict=True)

    return resultado


def parede_concreto_ano_mes_a_mes():
    """Totaliza o valor de parede de concreto no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, carteira_parede_de_concreto=True)
    resultado = completar_meses(pd.DataFrame(resultado), 'MES_EMISSAO', to_dict=True)

    return resultado


def eolicas_ano_mes_a_mes():
    """Totaliza o valor das eolicas no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, informacao_estrategica=19)
    resultado = completar_meses(pd.DataFrame(resultado), 'MES_EMISSAO', to_dict=True)

    return resultado


def ticket_medio_ano_mes_a_mes():
    """Totaliza o ticket medio das notas no periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_documento=True,)

    resultado = pd.DataFrame(resultado)
    resultado = resultado.groupby('MES_EMISSAO').agg(VALOR_MERCADORIAS=('VALOR_MERCADORIAS', 'sum'),
                                                     MEDIANA_PEDIDO=('VALOR_MERCADORIAS', 'median'),).reset_index()
    resultado = resultado.to_dict(orient='records')

    return resultado


# Não trocado para get_relatorios_vendas, muito especifico
def vec_antes_depois_visita_ano_mes_a_mes():
    """Totaliza o valor dos orçamentos de clientes visitados antes e depois do periodo informado em site setup mes a
    mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            GRUPOS_VISITAS.MES,
            SUM(CASE WHEN ORCAMENTOS.DATA_PEDIDO IS NULL THEN 0 WHEN ORCAMENTOS.DATA_PEDIDO BETWEEN GRUPOS_VISITAS.DATA_REALIZADO - 90 AND GRUPOS_VISITAS.DATA_REALIZADO THEN ORCAMENTOS.VALOR_TOTAL - ORCAMENTOS.VALOR_FRETE_INCL_ITEM ELSE 0 END) AS ANTES_ORCAMENTOS,
            SUM(CASE WHEN ORCAMENTOS.DATA_PEDIDO IS NULL THEN 0 WHEN ORCAMENTOS.DATA_PEDIDO BETWEEN GRUPOS_VISITAS.DATA_REALIZADO + 1 AND GRUPOS_VISITAS.DATA_REALIZADO + 90 THEN ORCAMENTOS.VALOR_TOTAL - ORCAMENTOS.VALOR_FRETE_INCL_ITEM ELSE 0 END) AS DEPOIS_ORCAMENTOS

        FROM
            (
                SELECT
                    PERIODO.MES,
                    CLIENTES.CHAVE_GRUPOECONOMICO,
                    MAX(CLIENTES_HISTORICO.DATA_REALIZADO) AS DATA_REALIZADO

                FROM
                    COPLAS.CLIENTES_HISTORICO,
                    COPLAS.CLIENTES,
                    COPLAS.ESTADOS,
                    (
                        SELECT 12 AS MES, :ano + (12 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 11 AS MES, :ano + (11 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 10 AS MES, :ano + (10 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 9 AS MES, :ano + (9 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 8 AS MES, :ano + (8 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 7 AS MES, :ano + (7 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 6 AS MES, :ano + (6 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 5 AS MES, :ano + (5 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 4 AS MES, :ano + (4 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 3 AS MES, :ano + (3 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 2 AS MES, :ano + (2 - 2) / 12.00 AS ANOMES FROM DUAL UNION ALL
                        SELECT 1 AS MES, :ano + (1 - 2) / 12.00 AS ANOMES FROM DUAL
                    ) PERIODO

                WHERE
                    CLIENTES.CODCLI = CLIENTES_HISTORICO.CHAVE_CLIENTE(+) AND
                    CLIENTES.UF = ESTADOS.CHAVE AND
                    CLIENTES.CHAVE_GRUPOECONOMICO IS NOT NULL AND
                    CLIENTES.CHAVE_GRUPOECONOMICO != 1 AND
                    ESTADOS.SIGLA = 'SP' AND
                    (
                        CLIENTES_HISTORICO.TIPO IN ('VISITA-INFORMACAO', 'VISITA-OPORTUNIDADE') AND
                        EXTRACT(YEAR FROM CLIENTES_HISTORICO.DATA_REALIZADO) + EXTRACT(MONTH FROM CLIENTES_HISTORICO.DATA_REALIZADO) / 12 = PERIODO.ANOMES AND
                        PERIODO.MES <= :mes
                        OR
                        CLIENTES_HISTORICO.CHAVE IS NULL
                    )

                GROUP BY
                    PERIODO.MES,
                    CLIENTES.CHAVE_GRUPOECONOMICO

                HAVING
                    MAX(CLIENTES_HISTORICO.DATA_REALIZADO) IS NOT NULL
            ) GRUPOS_VISITAS,
            COPLAS.CLIENTES,
            COPLAS.ESTADOS,
            COPLAS.ORCAMENTOS

        WHERE
            CLIENTES.UF = ESTADOS.CHAVE AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE(+) AND
            CLIENTES.CHAVE_GRUPOECONOMICO = GRUPOS_VISITAS.CHAVE_GRUPOECONOMICO AND
            ESTADOS.SIGLA = 'SP' AND
            ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM')

        GROUP BY
            GRUPOS_VISITAS.MES

        ORDER BY
            GRUPOS_VISITAS.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    return resultado


def quantidade_notas_ano_mes_a_mes():
    """Totaliza a quantidede de notas de saida emitidas do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_quantidade_documentos=True, especie='S',)

    resultado = pd.DataFrame(resultado)
    resultado = resultado[['MES_EMISSAO', 'QUANTIDADE_DOCUMENTOS']]
    resultado = resultado.to_dict(orient='records')

    return resultado


def produtividade_ano_mes_a_mes():
    """Totaliza a produtividade do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO) AS MES,
            ROUND(SUM(APONTAMENTOS.PRODUCAO_LIQUIDA * PRODUTOS.PESO_LIQUIDO) / SUM(APONTAMENTOS.TEMPO * PROCESSOS_OPERACOES.PECAS_MINUTO * PRODUTOS.PESO_LIQUIDO) * 100, 2) * (-1) + 100 AS PRODUTIV_POR_CENTO

        FROM
            COPLAS.PRODUTOS,
            COPLAS.PROCESSOS_OPERACOES,
            COPLAS.PROCESSOS,
            COPLAS.APONTAMENTOS,
            COPLAS.ORDENS

        WHERE
            ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM AND
            ORDENS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
            PROCESSOS_OPERACOES.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
            PRODUTOS.CPROD = ORDENS.CHAVE_PRODUTO AND
            APONTAMENTOS.CHAVE_SETOR = 3 AND
            PROCESSOS_OPERACOES.CHAVE_SETOR = 3 AND
            ORDENS.CHAVE_JOB = 22 AND
            ORDENS.CHAVE != 20658 AND

            TRUNC(APONTAMENTOS.INICIO) >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
            TRUNC(APONTAMENTOS.INICIO) <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)

        ORDER BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def peso_faturado_abc_ano_mes_a_mes():
    """Totaliza o peso faturado por classe ABC (todas as notas com CFOP de baixa de estoque) do periodo informado em
    site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    total = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                  coluna_mes_emissao=True, coluna_peso_produto_proprio=True,
                                  incluir_sem_valor_comercial=True, cfop_baixa_estoque=True,)
    total = pd.DataFrame(total)
    total = total[['MES_EMISSAO', 'PESO_PP']]
    total = total.rename(columns={'PESO_PP': 'TOTAL'})

    estoque_a = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_peso_produto_proprio=True,
                                      incluir_sem_valor_comercial=True, cfop_baixa_estoque=True, estoque_abc='A')
    estoque_a = pd.DataFrame(estoque_a)
    estoque_a = estoque_a[['MES_EMISSAO', 'PESO_PP']]
    estoque_a = estoque_a.rename(columns={'PESO_PP': 'A'})

    estoque_b = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_peso_produto_proprio=True,
                                      incluir_sem_valor_comercial=True, cfop_baixa_estoque=True, estoque_abc='B')
    estoque_b = pd.DataFrame(estoque_b)
    estoque_b = estoque_b[['MES_EMISSAO', 'PESO_PP']]
    estoque_b = estoque_b.rename(columns={'PESO_PP': 'B'})

    estoque_c = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_peso_produto_proprio=True,
                                      incluir_sem_valor_comercial=True, cfop_baixa_estoque=True, estoque_abc='C')
    estoque_c = pd.DataFrame(estoque_c)
    estoque_c = estoque_c[['MES_EMISSAO', 'PESO_PP']]
    estoque_c = estoque_c.rename(columns={'PESO_PP': 'C'})

    resultado = pd.merge(total, estoque_a, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, estoque_b, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, estoque_c, how='outer', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')

    return resultado


def peso_estoque_abc_ano_mes_a_mes():
    """Totaliza o peso do estoque por classe ABC do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            ULTIMA_MOVIMENTACAO.MES,
            ROUND(SUM(MOVESTOQUE.SALDO_ESTOQUE * PRODUTOS.PESO_LIQUIDO), 2) AS PESO_ESTOQUE_KG,
            ROUND(SUM(CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN MOVESTOQUE.SALDO_ESTOQUE * PRODUTOS.PESO_LIQUIDO ELSE 0 END), 2) AS PESO_ESTOQUE_KG_A,
            ROUND(SUM(CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN MOVESTOQUE.SALDO_ESTOQUE * PRODUTOS.PESO_LIQUIDO ELSE 0 END), 2) AS PESO_ESTOQUE_KG_B,
            ROUND(SUM(CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN MOVESTOQUE.SALDO_ESTOQUE * PRODUTOS.PESO_LIQUIDO ELSE 0 END), 2) AS PESO_ESTOQUE_KG_C

        FROM
            COPLAS.MOVESTOQUE,
            COPLAS.ALMOXARIFADOS,
            COPLAS.PRODUTOS,
            (
                SELECT
                    PERIODO.MES,
                    MAX(MOVESTOQUE.CHAVE) ULTIMA_MOVIMENTACAO

                FROM
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
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
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND

                    EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND
                    EXISTS(SELECT PRODUTOS.CPROD FROM COPLAS.PRODUTOS WHERE PRODUTOS.CHAVE_FAMILIA = 7766 AND PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO) AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES,
                    MOVESTOQUE.CHAVE_PRODUTO
            ) ULTIMA_MOVIMENTACAO

        WHERE
            ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO = MOVESTOQUE.CHAVE AND
            PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
            ALMOXARIFADOS.CHAVE_JOB = 22 AND
            PRODUTOS.CHAVE_FAMILIA = 7766

        GROUP BY
            ULTIMA_MOVIMENTACAO.MES

        ORDER BY
            ULTIMA_MOVIMENTACAO.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    return resultado


def setups_dia_ano_mes_a_mes():
    """Totaliza a media de setups por dia do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO) AS MES,
            ROUND(COUNT(APONTAMENTOS_PARADAS.CHAVE) / COUNT(DISTINCT EXTRACT(DAY FROM APONTAMENTOS_PARADAS.INICIO)), 0) AS SETUPS_DIA

        FROM
            COPLAS.PARADAS,
            COPLAS.APONTAMENTOS_PARADAS

        WHERE
            PARADAS.CHAVE = APONTAMENTOS_PARADAS.CHAVE_PARADA AND
            APONTAMENTOS_PARADAS.CHAVE_JOB = 22 AND
            PARADAS.DESCRICAO = 'SET-UP' AND

            TRUNC(APONTAMENTOS_PARADAS.INICIO) >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
            TRUNC(APONTAMENTOS_PARADAS.INICIO) <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO)

        ORDER BY
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def horas_improdutivas_ano_mes_a_mes():
    """Totaliza as horas improdutivas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO) AS MES,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('SET-UP') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS SETUP,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('MANUTENCAO DE MOLDE', 'FALTA DE OPCAO DE MOLDE') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS MOLDE,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('MANUTENCAO DE MAQUINA CORRETIVA') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS MAQUINA,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('OUTROS') AND APONTAMENTOS_PARADAS.OBSERVACOES LIKE '%CHIL%' THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS CHILLER,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('FALTA DE ENERGIA ELETRICA') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS ENERGIA,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('PROBLEMAS PIOVAN') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS PIOVAN,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('MANUTENCAO DE GELADEIRA', 'MATERIA PRIMA') OR PARADAS.DESCRICAO IN ('OUTROS') AND APONTAMENTOS_PARADAS.OBSERVACOES NOT LIKE '%CHIL%' THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS OUTROS,
            ROUND(SUM(CASE WHEN PARADAS.DESCRICAO IN ('PARADA ESTRATEGICA') THEN APONTAMENTOS_PARADAS.TEMPO / 60 ELSE 0 END), 2) AS PARADA_ESTRATEGICA

        FROM
            COPLAS.PARADAS,
            COPLAS.APONTAMENTOS_PARADAS

        WHERE
            PARADAS.CHAVE = APONTAMENTOS_PARADAS.CHAVE_PARADA AND
            APONTAMENTOS_PARADAS.CHAVE_JOB = 22 AND

            APONTAMENTOS_PARADAS.INICIO >= TO_DATE(:data_ano_inicio, 'DD-MM-YY') AND
            APONTAMENTOS_PARADAS.INICIO <= TO_DATE(:data_ano_fim, 'DD-MM-YY')

        GROUP BY
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO)

        ORDER BY
            EXTRACT(MONTH FROM APONTAMENTOS_PARADAS.INICIO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


# TODO: trocar para get_relatorios_financeiros
def inadimplencia_detalhe_ano_mes_a_mes():
    """Totaliza a inadimplencia detalhada por cliente do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            INAD.MES,
            INAD.NOMERED AS CLIENTE,
            INAD.EM_ABERTO,
            INAD.EM_ABERTO_MES,
            ROUND(INAD.EM_ABERTO / INAD.EM_ABERTO_MES * 100, 2) AS EM_ABERTO_PORCENTO_MES

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM RECEBER.DATAVENCIMENTO) AS MES,
                    CLIENTES.NOMERED,
                    SUM(RECEBER.VALORTOTAL - RECEBER.ABATIMENTOS_DEVOLUCOES - RECEBER.ABATIMENTOS_OUTROS - COALESCE(RECEBER.DESCONTOS, 0)) AS EM_ABERTO,
                    SUM(SUM(RECEBER.VALORTOTAL - RECEBER.ABATIMENTOS_DEVOLUCOES - RECEBER.ABATIMENTOS_OUTROS - COALESCE(RECEBER.DESCONTOS, 0))) OVER (PARTITION BY EXTRACT(MONTH FROM RECEBER.DATAVENCIMENTO)) AS EM_ABERTO_MES

                FROM
                    COPLAS.RECEBER,
                    COPLAS.RECEBER_JOB,
                    COPLAS.CLIENTES

                WHERE
                    RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND
                    RECEBER.CODCLI = CLIENTES.CODCLI AND
                    RECEBER_JOB.CHAVE_JOB = 22 AND
                    RECEBER.CONDICAO = 'EM ABERTO' AND

                    RECEBER.DATAVENCIMENTO >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
                    RECEBER.DATAVENCIMENTO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM RECEBER.DATAVENCIMENTO),
                    CLIENTES.NOMERED

                HAVING
                    SUM(RECEBER.VALORTOTAL - RECEBER.ABATIMENTOS_DEVOLUCOES - RECEBER.ABATIMENTOS_OUTROS - COALESCE(RECEBER.DESCONTOS, 0)) > 0
            ) INAD

        ORDER BY
            INAD.MES,
            EM_ABERTO_PORCENTO_MES DESC
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def inadimplencia_ano_mes_a_mes():
    """Totaliza a inadimplencia do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    receber_total = get_relatorios_financeiros('receber', data_vencimento_inicio=data_ano_inicio,
                                               data_vencimento_fim=data_ano_fim, coluna_mes_vencimento=True,
                                               coluna_valor_titulo_liquido_desconto=True,
                                               job=22,)
    receber_total = completar_meses(pd.DataFrame(receber_total), 'MES_VENCIMENTO')
    if 'VALOR_LIQUIDO_DESCONTOS' not in receber_total.columns:  # type:ignore
        receber_total['VALOR_LIQUIDO_DESCONTOS'] = 0  # type:ignore
    receber_total = receber_total.rename(columns={'VALOR_LIQUIDO_DESCONTOS': 'TOTAL_A_RECEBER',  # type:ignore
                                                  'VALOR_EFETIVO': 'LIQUIDADO'})

    em_aberto = get_relatorios_financeiros('receber', data_vencimento_inicio=data_ano_inicio,
                                           data_vencimento_fim=data_ano_fim, coluna_mes_vencimento=True,
                                           coluna_valor_titulo_liquido_desconto=True,
                                           job=22, condicao='EM ABERTO')
    em_aberto = completar_meses(pd.DataFrame(em_aberto), 'MES_VENCIMENTO')
    if 'VALOR_LIQUIDO_DESCONTOS' not in em_aberto.columns:  # type:ignore
        em_aberto['VALOR_LIQUIDO_DESCONTOS'] = 0  # type:ignore
    em_aberto = em_aberto.rename(columns={'VALOR_LIQUIDO_DESCONTOS': 'EM_ABERTO', })  # type:ignore
    em_aberto = em_aberto.drop(columns='VALOR_EFETIVO')

    em_cobranca = get_relatorios_financeiros('receber', data_vencimento_inicio=data_ano_inicio,
                                             data_vencimento_fim=data_ano_fim, coluna_mes_vencimento=True,
                                             coluna_valor_titulo_liquido_desconto=True,
                                             job=22, condicao='EM ABERTO', carteira_cobranca='COB SIMPLES',)
    em_cobranca = completar_meses(pd.DataFrame(em_cobranca), 'MES_VENCIMENTO')
    if 'VALOR_LIQUIDO_DESCONTOS' not in em_cobranca.columns:  # type:ignore
        em_cobranca['VALOR_LIQUIDO_DESCONTOS'] = 0  # type:ignore
    em_cobranca = em_cobranca.rename(columns={'VALOR_LIQUIDO_DESCONTOS': 'EM_COBRANCA', })  # type:ignore
    em_cobranca = em_cobranca.drop(columns='VALOR_EFETIVO')

    em_cartorio = get_relatorios_financeiros('receber', data_vencimento_inicio=data_ano_inicio,
                                             data_vencimento_fim=data_ano_fim, coluna_mes_vencimento=True,
                                             coluna_valor_titulo_liquido_desconto=True,
                                             job=22, condicao='EM ABERTO', carteira_cobranca='EM CARTORIO',)
    em_cartorio = completar_meses(pd.DataFrame(em_cartorio), 'MES_VENCIMENTO')
    if 'VALOR_LIQUIDO_DESCONTOS' not in em_cartorio.columns:  # type:ignore
        em_cartorio['VALOR_LIQUIDO_DESCONTOS'] = 0  # type:ignore
    em_cartorio = em_cartorio.rename(columns={'VALOR_LIQUIDO_DESCONTOS': 'EM_CARTORIO', })  # type:ignore
    em_cartorio = em_cartorio.drop(columns='VALOR_EFETIVO')

    resultado = pd.merge(receber_total, em_aberto, how='inner', on='MES_VENCIMENTO')
    resultado = pd.merge(resultado, em_cobranca, how='inner', on='MES_VENCIMENTO')
    resultado = pd.merge(resultado, em_cartorio, how='inner', on='MES_VENCIMENTO')

    resultado = resultado.to_dict(orient='records')  # type:ignore

    return resultado


def lucro_ano_mes_a_mes():
    """Totaliza o lucro do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    total = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                  coluna_mes_emissao=True, coluna_rentabilidade=True,)
    total = pd.DataFrame(total)
    total = total[['MES_EMISSAO', 'MC']]
    total = total.rename(columns={'MC': 'TOTAL'})

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_rentabilidade=True,
                               familia_produto=7766,)
    pp = pd.DataFrame(pp)
    pp = pp[['MES_EMISSAO', 'MC']]
    pp = pp.rename(columns={'MC': 'PP'})

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_rentabilidade=True,
                               familia_produto=[7767, 12441,],)
    pt = pd.DataFrame(pt)
    pt = pt[['MES_EMISSAO', 'MC']]
    pt = pt.rename(columns={'MC': 'PT'})

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_rentabilidade=True,
                               familia_produto=8378,)
    pq = pd.DataFrame(pq)
    pq = pq[['MES_EMISSAO', 'MC']]
    pq = pq.rename(columns={'MC': 'PQ'})

    resultado = pd.merge(total, pp, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pt, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pq, how='outer', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')

    return resultado


def peso_embalado_produto_proprio_ano_mes_a_mes():
    """Totaliza o peso embalado de produto proprio do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO) AS MES,
            ROUND(SUM(APONTAMENTOS.PRODUCAO_LIQUIDA * PRODUTOS.PESO_LIQUIDO), 4) AS EMBALADO_KG

        FROM
            COPLAS.PRODUTOS,
            COPLAS.PROCESSOS_OPERACOES,
            COPLAS.PROCESSOS,
            COPLAS.APONTAMENTOS,
            COPLAS.ORDENS

        WHERE
            ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM AND
            ORDENS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
            PROCESSOS_OPERACOES.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
            PRODUTOS.CPROD = ORDENS.CHAVE_PRODUTO AND
            APONTAMENTOS.CHAVE_SETOR = 12 AND
            PROCESSOS_OPERACOES.CHAVE_SETOR = 12 AND
            ORDENS.CHAVE_JOB = 22 AND
            PRODUTOS.CHAVE_FAMILIA = 7766 AND

            TRUNC(APONTAMENTOS.INICIO) >= TO_DATE(:data_ano_inicio, 'DD-MM-YYYY') AND
            TRUNC(APONTAMENTOS.INICIO) <= TO_DATE(:data_ano_fim, 'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)

        ORDER BY
            EXTRACT(MONTH FROM APONTAMENTOS.INICIO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def peso_materia_prima_produto_proprio_detalhe_ano_mes_a_mes():
    """Totaliza o peso da materia prima de produto proprio detalhado do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            ULTIMA_MOVIMENTACAO.MES,
            MATERIAIS.CODIGO,
            SUM(MOVESTOQUE.SALDO_ESTOQUE * MATERIAIS.PESO_LIQUIDO) / 1000 AS PESO_MP_ESTOQUE_TON

        FROM
            COPLAS.MOVESTOQUE,
            COPLAS.ALMOXARIFADOS,
            (
                SELECT DISTINCT
                    MATERIAIS.CPROD,
                    MATERIAIS.CODIGO,
                    MATERIAIS.PESO_LIQUIDO

                FROM
                    COPLAS.PRODUTOS MATERIAIS,
                    COPLAS.PRODUTOS,
                    COPLAS.PROCESSOS_MATERIAIS,
                    COPLAS.PROCESSOS

                WHERE
                    PROCESSOS_MATERIAIS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
                    PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    MATERIAIS.CPROD = PROCESSOS_MATERIAIS.CHAVE_MATERIAL AND
                    PRODUTOS.CHAVE_FAMILIA = 7766 AND
                    MATERIAIS.CHAVE_GRUPO = 8273
            ) MATERIAIS,
            (
                SELECT
                    PERIODO.MES,
                    MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                FROM
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
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
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND

                    EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND
                    EXISTS(SELECT PRODUTOS.CPROD FROM COPLAS.PRODUTOS WHERE PRODUTOS.CHAVE_GRUPO = 8273 AND PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO) AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES,
                    MOVESTOQUE.CHAVE_PRODUTO
            ) ULTIMA_MOVIMENTACAO

        WHERE
            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
            ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO = MOVESTOQUE.CHAVE AND
            MATERIAIS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
            ALMOXARIFADOS.CHAVE_JOB = 22 AND
            MOVESTOQUE.SALDO_ESTOQUE != 0

        GROUP BY
            ULTIMA_MOVIMENTACAO.MES,
            MATERIAIS.CODIGO

        ORDER BY
            ULTIMA_MOVIMENTACAO.MES,
            MATERIAIS.CODIGO
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    return resultado


def peso_materia_prima_produto_proprio_ano_mes_a_mes():
    """Totaliza o peso da materia prima de produto proprio do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            ULTIMA_MOVIMENTACAO.MES,
            SUM(MOVESTOQUE.SALDO_ESTOQUE * MATERIAIS.PESO_LIQUIDO) AS PESO_MP_ESTOQUE_KG

        FROM
            COPLAS.MOVESTOQUE,
            COPLAS.ALMOXARIFADOS,
            (
                SELECT DISTINCT
                    MATERIAIS.CPROD,
                    MATERIAIS.PESO_LIQUIDO

                FROM
                    COPLAS.PRODUTOS MATERIAIS,
                    COPLAS.PRODUTOS,
                    COPLAS.PROCESSOS_MATERIAIS,
                    COPLAS.PROCESSOS

                WHERE
                    PROCESSOS_MATERIAIS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
                    PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    MATERIAIS.CPROD = PROCESSOS_MATERIAIS.CHAVE_MATERIAL AND
                    PRODUTOS.CHAVE_FAMILIA = 7766 AND
                    MATERIAIS.CHAVE_GRUPO = 8273
            ) MATERIAIS,
            (
                SELECT
                    PERIODO.MES,
                    MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                FROM
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
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
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND

                    EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND
                    EXISTS(SELECT PRODUTOS.CPROD FROM COPLAS.PRODUTOS WHERE PRODUTOS.CHAVE_GRUPO = 8273 AND PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO) AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES,
                    MOVESTOQUE.CHAVE_PRODUTO
            ) ULTIMA_MOVIMENTACAO

        WHERE
            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
            ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO = MOVESTOQUE.CHAVE AND
            MATERIAIS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
            ALMOXARIFADOS.CHAVE_JOB = 22

        GROUP BY
            ULTIMA_MOVIMENTACAO.MES

        ORDER BY
            ULTIMA_MOVIMENTACAO.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    return resultado


def peso_faturado_produto_proprio_ano_mes_a_mes():
    """Totaliza o peso faturado de produto proprio (todas as notas com CFOP de baixa de estoque) do periodo informado
    em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    resultado = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                      coluna_mes_emissao=True, coluna_peso_produto_proprio=True,
                                      incluir_sem_valor_comercial=True, cfop_baixa_estoque=True,)
    resultado = pd.DataFrame(resultado)
    resultado = resultado[['MES_EMISSAO', 'PESO_PP']]
    resultado = resultado.to_dict(orient='records')

    return resultado


def peso_estoque_produto_proprio_ano_mes_a_mes():
    """Totaliza o peso do estoque de produto proprio do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql = """
        SELECT
            ULTIMA_MOVIMENTACAO.MES,
            SUM(MOVESTOQUE.SALDO_ESTOQUE * PRODUTOS.PESO_LIQUIDO) AS PESO_ESTOQUE_KG

        FROM
            COPLAS.MOVESTOQUE,
            COPLAS.ALMOXARIFADOS,
            COPLAS.PRODUTOS,
            (
                SELECT
                    PERIODO.MES,
                    MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                FROM
                    COPLAS.PRODUTOS,
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
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
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
                    PRODUTOS.CHAVE_FAMILIA = 7766 AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND
                    EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES,
                    PRODUTOS.CPROD
            ) ULTIMA_MOVIMENTACAO

        WHERE
            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
            MOVESTOQUE.CHAVE = ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO AND
            PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
            ALMOXARIFADOS.CHAVE_JOB = 22 AND
            PRODUTOS.CHAVE_FAMILIA = 7766

        GROUP BY
            ULTIMA_MOVIMENTACAO.MES

        ORDER BY
            ULTIMA_MOVIMENTACAO.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes)

    return resultado


def insvestimento_retiradas_ano_mes_a_mes():
    """Totaliza os investimentos e retiradas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    investimentos_total = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_ano_inicio,
                                                     data_liquidacao_fim=data_ano_fim, coluna_mes_liquidacao=True,
                                                     job=22, centro_resultado_coplas=True, plano_conta_codigo='4.%',)
    investimentos_total = completar_meses(pd.DataFrame(investimentos_total), 'MES_LIQUIDACAO')
    if 'VALOR_EFETIVO' not in investimentos_total.columns:  # type:ignore
        investimentos_total['VALOR_EFETIVO'] = 0  # type:ignore
    investimentos_total = investimentos_total.rename(columns={'VALOR_EFETIVO': 'INVESTIMENTOS_TOTAL'})  # type:ignore

    retiradas = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_ano_inicio,
                                           data_liquidacao_fim=data_ano_fim, coluna_mes_liquidacao=True,
                                           job=22, centro_resultado_coplas=True, plano_conta_codigo='4.02.01.001',)
    retiradas = completar_meses(pd.DataFrame(retiradas), 'MES_LIQUIDACAO')
    if 'VALOR_EFETIVO' not in retiradas.columns:  # type:ignore
        retiradas['VALOR_EFETIVO'] = 0  # type:ignore
    retiradas = retiradas.rename(columns={'VALOR_EFETIVO': 'RETIRADA_C'})  # type:ignore

    investimentos_o3 = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_ano_inicio,
                                                  data_liquidacao_fim=data_ano_fim, coluna_mes_liquidacao=True,
                                                  job=22, centro_resultado=41,)
    investimentos_o3 = completar_meses(pd.DataFrame(investimentos_o3), 'MES_LIQUIDACAO')
    if 'VALOR_EFETIVO' not in investimentos_o3.columns:  # type:ignore
        investimentos_o3['VALOR_EFETIVO'] = 0  # type:ignore
    investimentos_o3 = investimentos_o3.rename(columns={'VALOR_EFETIVO': 'INVESTIMENTO_3_O'})  # type:ignore

    investimentos_fluxus = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_ano_inicio,
                                                      data_liquidacao_fim=data_ano_fim, coluna_mes_liquidacao=True,
                                                      job=22, centro_resultado=48,)
    investimentos_fluxus = completar_meses(pd.DataFrame(investimentos_fluxus), 'MES_LIQUIDACAO')
    if 'VALOR_EFETIVO' not in investimentos_fluxus.columns:  # type:ignore
        investimentos_fluxus['VALOR_EFETIVO'] = 0  # type:ignore
    investimentos_fluxus = investimentos_fluxus.rename(columns={'VALOR_EFETIVO': 'INVESTIMENTO_FLUXUS'})  # type:ignore

    resultado = pd.merge(investimentos_total, retiradas, how='inner', on='MES_LIQUIDACAO')
    resultado['INVESTIMENTO_1_C'] = resultado['INVESTIMENTOS_TOTAL'] - resultado['RETIRADA_C']
    resultado = resultado[['MES_LIQUIDACAO', 'INVESTIMENTO_1_C', 'RETIRADA_C']]
    resultado = pd.merge(resultado, investimentos_o3, how='inner', on='MES_LIQUIDACAO')
    resultado = pd.merge(resultado, investimentos_fluxus, how='inner', on='MES_LIQUIDACAO')

    resultado = resultado.to_dict(orient='records')  # type:ignore

    return resultado


def imposto_faturado_ano_mes_a_mes():
    """Totaliza os impostos do faturamento do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_ipi=True, coluna_st=True, coluna_icms=True,
                               coluna_pis=True, coluna_cofins=True, coluna_irpj_csll=True,
                               coluna_icms_partilha=True, job=22,
                               familia_produto=7766,)
    pp = pd.DataFrame(pp)
    pp = pp[['MES_EMISSAO', 'IPI', 'ST', 'ICMS', 'PIS', 'COFINS', 'IRPJ_CSLL', 'ICMS_PARTILHA',]]
    pp = pp.rename(columns={'IPI': 'IPI_PP', 'ST': 'ST_PP', 'ICMS': 'ICMS_PP', 'PIS': 'PIS_PP', 'COFINS': 'COFINS_PP',
                            'IRPJ_CSLL': 'IRPJ_CSLL_PP', 'ICMS_PARTILHA': 'ICMS_PARTILHA_PP', })

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_ipi=True, coluna_st=True, coluna_icms=True,
                               coluna_pis=True, coluna_cofins=True, coluna_irpj_csll=True,
                               coluna_icms_partilha=True, job=22,
                               familia_produto=7767,)
    pt = pd.DataFrame(pt)
    pt = pt[['MES_EMISSAO', 'IPI', 'ST', 'ICMS', 'PIS', 'COFINS', 'IRPJ_CSLL', 'ICMS_PARTILHA',]]
    pt = pt.rename(columns={'IPI': 'IPI_PT', 'ST': 'ST_PT', 'ICMS': 'ICMS_PT', 'PIS': 'PIS_PT', 'COFINS': 'COFINS_PT',
                            'IRPJ_CSLL': 'IRPJ_CSLL_PT', 'ICMS_PARTILHA': 'ICMS_PARTILHA_PT', })

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_ipi=True, coluna_st=True, coluna_icms=True,
                               coluna_pis=True, coluna_cofins=True, coluna_irpj_csll=True,
                               coluna_icms_partilha=True, job=22,
                               familia_produto=8378,)
    pq = pd.DataFrame(pq)
    pq = pq[['MES_EMISSAO', 'IPI', 'ST', 'ICMS', 'PIS', 'COFINS', 'IRPJ_CSLL', 'ICMS_PARTILHA',]]
    pq = pq.rename(columns={'IPI': 'IPI_PQ', 'ST': 'ST_PQ', 'ICMS': 'ICMS_PQ', 'PIS': 'PIS_PQ', 'COFINS': 'COFINS_PQ',
                            'IRPJ_CSLL': 'IRPJ_CSLL_PQ', 'ICMS_PARTILHA': 'ICMS_PARTILHA_PQ', })

    resultado = pd.merge(pp, pt, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pq, how='outer', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')

    return resultado


def faturado_mercadorias_ano_mes_a_mes(*, mes_atual: bool = False):
    """Totaliza o faturamento do valor das mercadorias do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        if not mes_atual:
            data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
            data_ano_fim = site_setup.atualizacoes_data_mes_fim
        else:
            data_ano_inicio = site_setup.primeiro_dia_mes
            data_ano_fim = site_setup.ultimo_dia_mes

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, familia_produto=7766,)
    pp = pd.DataFrame(pp)
    pp = pp.rename(columns={'VALOR_MERCADORIAS': 'PP'})

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, familia_produto=[7767, 12441,],)
    pt = pd.DataFrame(pt)
    pt = pt.rename(columns={'VALOR_MERCADORIAS': 'PT'})

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, familia_produto=8378,)
    pq = pd.DataFrame(pq)
    pq = pq.rename(columns={'VALOR_MERCADORIAS': 'PQ'})

    total = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                  coluna_mes_emissao=True,)
    total = pd.DataFrame(total)
    total = total.rename(columns={'VALOR_MERCADORIAS': 'TOTAL'})

    resultado = pd.merge(pp, pt, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pq, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, total, how='outer', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')

    if mes_atual and resultado:
        resultado = resultado[0]

    return resultado


def faturado_bruto_ano_mes_a_mes(*, mes_atual: bool = False):
    """Totaliza o faturamento bruto do periodo informado em site setup mes a mes"""
    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        if not mes_atual:
            data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
            data_ano_fim = site_setup.atualizacoes_data_mes_fim
        else:
            data_ano_inicio = site_setup.primeiro_dia_mes
            data_ano_fim = site_setup.ultimo_dia_mes

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_valor_bruto=True, familia_produto=7766, job=22,)
    pp = pd.DataFrame(pp)
    pp = pp[['MES_EMISSAO', 'VALOR_BRUTO']]
    pp = pp.rename(columns={'VALOR_BRUTO': 'FATURADO_PP'})

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_valor_bruto=True, familia_produto=7767, job=22,)
    pt = pd.DataFrame(pt)
    pt = pt[['MES_EMISSAO', 'VALOR_BRUTO']]
    pt = pt.rename(columns={'VALOR_BRUTO': 'FATURADO_PT'})

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_valor_bruto=True, familia_produto=8378, job=22,)
    pq = pd.DataFrame(pq)
    pq = pq[['MES_EMISSAO', 'VALOR_BRUTO']]
    pq = pq.rename(columns={'VALOR_BRUTO': 'FATURADO_PQ'})

    total = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                  coluna_mes_emissao=True, coluna_valor_bruto=True, job=22,)
    total = pd.DataFrame(total)
    total = total[['MES_EMISSAO', 'VALOR_BRUTO']]
    total = total.rename(columns={'VALOR_BRUTO': 'FATURADO_TOTAL'})

    resultado = pd.merge(pp, pt, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pq, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, total, how='outer', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')

    if mes_atual and resultado:
        resultado = resultado[0]

    return resultado


# TODO: trocar para get_relatorios_financeiros
def despesa_variavel_ano_mes_a_mes():
    """Totaliza a despesa variavel do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
            ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.03.%' OR PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' OR PLANO_DE_CONTAS.CONTA LIKE '2.05.03.004' THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END), 2) AS RATEAR_PP_PT_PQ,
            ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.03.%' AND PAGAR.CODFOR IN (19786, 19688) OR PLANO_DE_CONTAS.CONTA LIKE '2.05.03.004' THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SOMENTE_PT,
            ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.01.03.%' AND PAGAR.CODFOR IN (19476) THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS SOMENTE_PQ,
            ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' AND PAGAR_CENTRORESULTADO.CHAVE_CENTRO != 47 THEN PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 ELSE 0 END), 2) AS RATEAR_PP_PT

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
            PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
            PAGAR_JOB.CHAVE_JOB = 22 AND
            PLANO_DE_CONTAS.CONTA LIKE '2.%' AND
            PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.01.%' AND
            PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.02.%' AND
            PLANO_DE_CONTAS.CONTA NOT LIKE '2.03.%' AND

            PAGAR.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
            PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

        GROUP BY
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)

        ORDER BY
            EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


# TODO: trocar para get_relatorios_financeiros
def despesa_operacional_ano_mes_a_mes():
    """Totaliza a despesa operacional do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            DO.MES,
            SUM(DO.DO) AS DO

        FROM
            (
                SELECT
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' AND PAGAR_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN 0 ELSE PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000 END), 2) AS DO

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
                    PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    PAGAR_JOB.CHAVE_JOB = 22 AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.01.%' AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.02.%' AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.03.%' AND
                    (
                        PLANO_DE_CONTAS.CONTA LIKE '2.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.%'
                    ) AND

                    PAGAR.DATALIQUIDACAO >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
                    PAGAR.DATALIQUIDACAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO)

                UNION ALL

                SELECT
                    EXTRACT(MONTH FROM MOVBAN.DATA) AS MES,
                    ROUND(SUM(CASE WHEN PLANO_DE_CONTAS.CONTA LIKE '2.02.02.%' AND MOVBAN_CENTRORESULTADO.CHAVE_CENTRO = 47 THEN 0 ELSE MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000 END), 2) AS DO

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
                    MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND
                    MOVBAN_JOB.CHAVE_JOB = 22 AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.01.%' AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.01.02.%' AND
                    PLANO_DE_CONTAS.CONTA NOT LIKE '2.03.%' AND
                    (
                        PLANO_DE_CONTAS.CONTA LIKE '2.%' OR
                        PLANO_DE_CONTAS.CONTA LIKE '3.%'
                    ) AND

                    MOVBAN.DATA >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
                    MOVBAN.DATA <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    EXTRACT(MONTH FROM MOVBAN.DATA)
            ) DO

        GROUP BY
            DO.MES

        ORDER BY
            DO.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


def custo_materia_prima_faturada_ano_mes_a_mes():
    """Totaliza o custo das materias primas dos produtos faturados do periodo informado em site setup mes a mes"""

    # Não funciona com a fluxus

    from dashboards.services import get_relatorios_vendas
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    pp = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7766,
                               job=22,)
    pp = pd.DataFrame(pp)
    pp = pp[['MES_EMISSAO', 'CUSTO_MP']]
    pp = pp.rename(columns={'CUSTO_MP': 'CUSTO_MP_PP'})

    pt = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7767,
                               job=22,)
    pt = pd.DataFrame(pt)
    pt = pt[['MES_EMISSAO', 'CUSTO_MP']]
    pt = pt.rename(columns={'CUSTO_MP': 'CUSTO_MP_PT'})

    pq = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                               coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=8378,
                               job=22,)
    pq = pd.DataFrame(pq)
    pq = pq[['MES_EMISSAO', 'CUSTO_MP']]
    pq = pq.rename(columns={'CUSTO_MP': 'CUSTO_MP_PQ'})

    nc4 = get_relatorios_vendas('faturamentos', inicio=data_ano_inicio, fim=data_ano_fim,
                                coluna_mes_emissao=True, coluna_custo_materia_prima_notas=True, familia_produto=7767,
                                job=22, produto_marca=181)
    nc4 = pd.DataFrame(nc4)
    nc4 = nc4[['MES_EMISSAO', 'CUSTO_MP']]
    nc4 = nc4.rename(columns={'CUSTO_MP': 'CUSTO_MP_NC4'})

    resultado = pd.merge(pp, pt, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, pq, how='outer', on='MES_EMISSAO')
    resultado = pd.merge(resultado, nc4, how='outer', on='MES_EMISSAO')
    resultado['CUSTO_MP_SEM_NC4'] = resultado['CUSTO_MP_PT'] - resultado['CUSTO_MP_NC4']
    resultado = resultado.to_dict(orient='records')

    return resultado


def custo_materia_prima_estoque_acabado_ano_mes_a_mes():
    """Totaliza o custo de materia prime dos produtos acabados no estoque do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano

    sql_custo_mp = """
        SELECT
            ULTIMO_CUSTO.MES,
            PROCESSOS.CHAVE_PRODUTO,
            SUM(PROCESSOS_MATERIAIS.QUANTIDADE * CUSTOS_PRODUTOS_LOG.CUSTOT_NOVO) AS CUSTO_MP

        FROM
            COPLAS.PRODUTOS,
            COPLAS.PROCESSOS,
            COPLAS.PROCESSOS_MATERIAIS,
            COPLAS.PRODUTOS MATERIAIS,
            COPLAS.CUSTOS_PRODUTOS_LOG,
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
            PRODUTOS.CPROD = PROCESSOS.CHAVE_PRODUTO AND
            CUSTOS_PRODUTOS_LOG.CHAVE_PRODUTO = MATERIAIS.CPROD AND
            CUSTOS_PRODUTOS_LOG.CHAVE = ULTIMO_CUSTO.ULTIMO_CUSTO AND
            PROCESSOS.CHAVE = PROCESSOS_MATERIAIS.CHAVE_PROCESSO AND
            PROCESSOS_MATERIAIS.CHAVE_MATERIAL = MATERIAIS.CPROD AND
            PRODUTOS.CHAVE_FAMILIA = 7766 AND
            PROCESSOS.PADRAO = 'SIM' AND
            CUSTOS_PRODUTOS_LOG.CHAVE_JOB = 22

        GROUP BY
            ULTIMO_CUSTO.MES,
            PROCESSOS.CHAVE_PRODUTO
    """

    sql_estoque = """
        SELECT
            ULTIMA_MOVIMENTACAO.MES,
            PRODUTOS.CPROD,
            MOVESTOQUE.SALDO_ESTOQUE AS ESTOQUE_PP

        FROM
            COPLAS.MOVESTOQUE,
            COPLAS.ALMOXARIFADOS,
            COPLAS.PRODUTOS,
            (
                SELECT
                    PERIODO.MES,
                    MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                FROM
                    COPLAS.PRODUTOS,
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
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
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
                    PRODUTOS.CHAVE_FAMILIA = 7766 AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND
                    EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND

                    PERIODO.MES <= :mes

                GROUP BY
                    PERIODO.MES,
                    MOVESTOQUE.CHAVE_PRODUTO
            ) ULTIMA_MOVIMENTACAO

        WHERE
            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
            MOVESTOQUE.CHAVE = ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO AND
            PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
            PRODUTOS.CHAVE_FAMILIA = 7766 AND
            ALMOXARIFADOS.CHAVE_JOB = 22 AND
            MOVESTOQUE.SALDO_ESTOQUE > 0
    """

    resultado_custo_mp = executar_oracle(sql_custo_mp, exportar_cabecalho=True, mes=mes, ano=ano)

    resultado_estoque = executar_oracle(sql_estoque, exportar_cabecalho=True, mes=mes, ano=ano)

    resultado = [
        {
            'MES': 1,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 2,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 3,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 4,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 5,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 6,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 7,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 8,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 9,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 10,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 11,
            'CUSTO_MP_ESTOQUE': 0
        },
        {
            'MES': 12,
            'CUSTO_MP_ESTOQUE': 0
        },
    ]

    for estoque_produto in resultado_estoque:
        for custo_produto in resultado_custo_mp:
            if custo_produto['MES'] == estoque_produto['MES'] and custo_produto['CHAVE_PRODUTO'] == estoque_produto['CPROD']:
                i = custo_produto['MES'] - 1
                resultado[i]['CUSTO_MP_ESTOQUE'] += custo_produto['CUSTO_MP'] * estoque_produto['ESTOQUE_PP']
                resultado[i]['CUSTO_MP_ESTOQUE'] = round(resultado[i]['CUSTO_MP_ESTOQUE'], 2)
                break

    return resultado


def ativo_operacional_produto_acabado_ano_mes_a_mes():
    """Totaliza o ativo operacional dos produtos acabados do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        mes = site_setup.atualizacoes_mes
        ano = site_setup.atualizacoes_ano
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio_as_ddmmyyyy
        data_ano_fim = site_setup.atualizacoes_data_mes_fim_as_ddmmyyyy

    sql = """
        SELECT
            ESTOQUE.MES,
            ROUND(SUM(ESTOQUE.ESTOQUE_PP * COALESCE(PRECO_MEDIO.PRECO_MEDIO_PP, ESTOQUE.TABELA, 0)), 2) AS AO_PP,
            ROUND(SUM(ESTOQUE.ESTOQUE_PT * COALESCE(PRECO_MEDIO.PRECO_MEDIO_PT, ESTOQUE.TABELA, 0)), 2) AS AO_PT,
            ROUND(SUM(ESTOQUE.ESTOQUE_PQ * COALESCE(PRECO_MEDIO.PRECO_MEDIO_PQ, ESTOQUE.TABELA, 0)), 2) AS AO_PQ

        FROM
            (
                SELECT
                    ULTIMA_MOVIMENTACAO.MES,
                    PRODUTOS.CPROD,
                    PRODUTOS_JOBS_CUSTOS.PRECO_ICMS0 AS TABELA,
                    CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN MOVESTOQUE.SALDO_ESTOQUE ELSE 0 END AS ESTOQUE_PP,
                    CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN MOVESTOQUE.SALDO_ESTOQUE ELSE 0 END AS ESTOQUE_PT,
                    CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN MOVESTOQUE.SALDO_ESTOQUE ELSE 0 END AS ESTOQUE_PQ

                FROM
                    COPLAS.MOVESTOQUE,
                    COPLAS.ALMOXARIFADOS,
                    COPLAS.PRODUTOS,
                    COPLAS.PRODUTOS_JOBS_CUSTOS,
                    (
                        SELECT
                            PERIODO.MES,
                            MAX(MOVESTOQUE.CHAVE) AS ULTIMA_MOVIMENTACAO

                        FROM
                            COPLAS.MOVESTOQUE,
                            COPLAS.ALMOXARIFADOS,
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
                            MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                            ALMOXARIFADOS.CHAVE_JOB = 22 AND

                            EXTRACT(YEAR FROM MOVESTOQUE.DATA_MOV) + EXTRACT(MONTH FROM MOVESTOQUE.DATA_MOV) / 12.00 + EXTRACT(DAY FROM MOVESTOQUE.DATA_MOV) / 365.00 < PERIODO.ANOMESDIA AND

                            PERIODO.MES <= :mes

                        GROUP BY
                            PERIODO.MES,
                            MOVESTOQUE.CHAVE_PRODUTO
                    ) ULTIMA_MOVIMENTACAO

                WHERE
                    MOVESTOQUE.CHAVE_ALMOXARIFADO = ALMOXARIFADOS.CHAVE AND
                    PRODUTOS_JOBS_CUSTOS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    MOVESTOQUE.CHAVE = ULTIMA_MOVIMENTACAO.ULTIMA_MOVIMENTACAO AND
                    PRODUTOS.CPROD = MOVESTOQUE.CHAVE_PRODUTO AND
                    ALMOXARIFADOS.CHAVE_JOB = 22 AND
                    PRODUTOS_JOBS_CUSTOS.CHAVE_JOB = 22 AND
                    PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND
                    MOVESTOQUE.SALDO_ESTOQUE > 0
            ) ESTOQUE,
            (
                SELECT
                    PRODUTOS.CPROD,
                    ROUND(AVG(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.PRECO_FATURADO ELSE 0 END), 2) AS PRECO_MEDIO_PP,
                    ROUND(AVG(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.PRECO_FATURADO ELSE 0 END), 2) AS PRECO_MEDIO_PT,
                    ROUND(AVG(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.PRECO_FATURADO ELSE 0 END), 2) AS PRECO_MEDIO_PQ

                FROM
                    COPLAS.NOTAS,
                    COPLAS.NOTAS_ITENS,
                    COPLAS.PRODUTOS

                WHERE
                    PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
                    NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
                    NOTAS.VALOR_COMERCIAL = 'SIM' AND
                    NOTAS.ESPECIE = 'S' AND
                    PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378) AND
                    NOTAS.CHAVE_JOB = 22 AND

                    NOTAS.DATA_EMISSAO >= TO_DATE(:data_ano_inicio,'DD-MM-YYYY') AND
                    NOTAS.DATA_EMISSAO <= TO_DATE(:data_ano_fim,'DD-MM-YYYY')

                GROUP BY
                    PRODUTOS.CPROD
            ) PRECO_MEDIO

        WHERE
            ESTOQUE.CPROD = PRECO_MEDIO.CPROD(+)

        GROUP BY
            ESTOQUE.MES

        ORDER BY
            ESTOQUE.MES
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, ano=ano, mes=mes, data_ano_inicio=data_ano_inicio,
                                data_ano_fim=data_ano_fim)

    return resultado


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
            COPLAS.ORDENS,
            COPLAS.APONTAMENTOS

        WHERE
            APONTAMENTOS.CHAVE_ORDEM = ORDENS.CHAVE AND
            ORDENS.CHAVE_JOB = 22 AND
            APONTAMENTOS.CHAVE_SETOR = 3 AND

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

    return resultado


def frete_cif_ano_mes_a_mes(*, mes_atual: bool = False):
    """Totaliza o valor dos fretes CIF do periodo informado em site setup mes a mes. Parametro para sobreescrever a data das atualizações"""
    site_setup = get_site_setup()
    if site_setup:
        if not mes_atual:
            data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
            data_ano_fim = site_setup.atualizacoes_data_mes_fim
        else:
            data_ano_inicio = site_setup.primeiro_dia_mes
            data_ano_fim = site_setup.ultimo_dia_mes

    total = get_relatorios_financeiros('pagar', data_emissao_inicio=data_ano_inicio, data_emissao_fim=data_ano_fim,
                                       coluna_mes_emissao=True, coluna_valor_titulo=True, job=22,
                                       centro_resultado_coplas=True, plano_conta_frete_cif=True,)
    total = completar_meses(pd.DataFrame(total), 'MES_EMISSAO')
    if 'VALOR_TITULO' not in total.columns:  # type:ignore
        total['VALOR_TITULO'] = 0  # type:ignore

    agilli_total = get_relatorios_financeiros('pagar', data_emissao_inicio=data_ano_inicio, data_emissao_fim=data_ano_fim,
                                              coluna_mes_emissao=True, coluna_valor_titulo=True, job=22,
                                              fornecedor='%AGILLI BRASIL%',
                                              centro_resultado_coplas=True, plano_conta_frete_cif=True,)
    agilli_total = completar_meses(pd.DataFrame(agilli_total), 'MES_EMISSAO')
    if 'VALOR_TITULO' not in agilli_total.columns:  # type:ignore
        agilli_total['VALOR_TITULO'] = 0  # type:ignore

    agilli_real = get_relatorios_financeiros('pagar', data_emissao_inicio=data_ano_inicio, data_emissao_fim=data_ano_fim,
                                             coluna_mes_emissao=True, coluna_valor_titulo=True, job=22,
                                             fornecedor='%AGILLI BRASIL%', status_diferente='PREVISAO',
                                             centro_resultado_coplas=True, plano_conta_frete_cif=True,)
    agilli_real = completar_meses(pd.DataFrame(agilli_real), 'MES_EMISSAO')
    if 'VALOR_TITULO' not in agilli_real.columns:  # type:ignore
        agilli_real['VALOR_TITULO'] = 0  # type:ignore
    agilli_real = agilli_real.rename(columns={'VALOR_TITULO': 'AGILLI'})  # type:ignore

    resultado = pd.merge(total, agilli_total, how='inner', on='MES_EMISSAO')  # type:ignore
    resultado['OUTRAS_TRANSPORTADORAS'] = resultado['VALOR_TITULO_x'] - resultado['VALOR_TITULO_y']
    resultado = resultado.drop(columns=['VALOR_TITULO_x', 'VALOR_TITULO_y'])

    resultado = pd.merge(agilli_real, resultado, how='inner', on='MES_EMISSAO')
    resultado = resultado.to_dict(orient='records')  # type:ignore

    if mes_atual and resultado:
        resultado = resultado[data_ano_inicio.month - 1]

    return resultado


def financeiro_ano_mes_a_mes():
    """Totaliza o valor das grandes contas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    relatorios = []
    plano_contas = [
        ('1.%', 'RECEITAS'),
        ('2.%', 'CUSTOS_VARIAVEIS'),
        ('3.%', 'CUSTOS_FIXOS'),
        ('4.%', 'INVESTIMENTOS'),
    ]

    for codigo_plano, descricao_plano in plano_contas:
        pagar = get_relatorios_financeiros('pagar', coluna_mes_liquidacao=True, valor_debito_negativo=True,
                                           job=22, centro_resultado_coplas=True,
                                           data_liquidacao_inicio=data_ano_inicio,
                                           data_liquidacao_fim=data_ano_fim, plano_conta_codigo=codigo_plano)
        pagar = completar_meses(pd.DataFrame(pagar), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in pagar.columns:  # type:ignore
            pagar['VALOR_EFETIVO'] = 0  # type:ignore
        pagar = pagar.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        receber = get_relatorios_financeiros('receber', coluna_mes_liquidacao=True,
                                             job=22, centro_resultado_coplas=True,
                                             data_liquidacao_inicio=data_ano_inicio,
                                             data_liquidacao_fim=data_ano_fim, plano_conta_codigo=codigo_plano)
        receber = completar_meses(pd.DataFrame(receber), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in receber.columns:  # type:ignore
            receber['VALOR_EFETIVO'] = 0  # type:ignore
        receber = receber.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        pagar_receber = pd.merge(pagar, receber, how='inner', on='MES_LIQUIDACAO')
        pagar_receber[descricao_plano] = pagar_receber[descricao_plano + '_x'] + pagar_receber[descricao_plano + '_y']
        pagar_receber = pagar_receber.drop(columns=[descricao_plano + '_x', descricao_plano + '_y'])

        relatorios.append(pagar_receber)

    resultado = pd.DataFrame()
    for relatorio in relatorios:
        if resultado.empty:
            resultado = pd.DataFrame(relatorio)
            continue
        resultado = pd.merge(resultado, relatorio, how='inner', on='MES_LIQUIDACAO')

    resultado = resultado.to_dict(orient='records')

    return resultado


def financeiro_geral_ano_mes_a_mes():
    """Totaliza o valor geral das grandes contas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    relatorios = []
    plano_contas = [
        ('1.%', 'RECEITAS'),
        ('2.%', 'CUSTOS_VARIAVEIS'),
        ('3.%', 'CUSTOS_FIXOS'),
        ('4.%', 'INVESTIMENTOS'),
    ]

    for codigo_plano, descricao_plano in plano_contas:
        pagar = get_relatorios_financeiros('pagar', coluna_mes_liquidacao=True, valor_debito_negativo=True,
                                           data_liquidacao_inicio=data_ano_inicio,
                                           data_liquidacao_fim=data_ano_fim, plano_conta_codigo=codigo_plano)
        pagar = completar_meses(pd.DataFrame(pagar), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in pagar.columns:  # type:ignore
            pagar['VALOR_EFETIVO'] = 0  # type:ignore
        pagar = pagar.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        receber = get_relatorios_financeiros('receber', coluna_mes_liquidacao=True,
                                             data_liquidacao_inicio=data_ano_inicio,
                                             data_liquidacao_fim=data_ano_fim, plano_conta_codigo=codigo_plano)
        receber = completar_meses(pd.DataFrame(receber), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in receber.columns:  # type:ignore
            receber['VALOR_EFETIVO'] = 0  # type:ignore
        receber = receber.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        pagar_receber = pd.merge(pagar, receber, how='inner', on='MES_LIQUIDACAO')
        pagar_receber[descricao_plano] = pagar_receber[descricao_plano + '_x'] + pagar_receber[descricao_plano + '_y']
        pagar_receber = pagar_receber.drop(columns=[descricao_plano + '_x', descricao_plano + '_y'])

        relatorios.append(pagar_receber)

    resultado = pd.DataFrame()
    for relatorio in relatorios:
        if resultado.empty:
            resultado = pd.DataFrame(relatorio)
            continue
        resultado = pd.merge(resultado, relatorio, how='inner', on='MES_LIQUIDACAO')

    resultado = resultado.to_dict(orient='records')

    return resultado


# TODO: trocar para get_relatorios_financeiros
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
                    PAGAR_JOB.CHAVE_JOB = 22 AND
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
                    RECEBER_JOB.CHAVE_JOB = 22 AND
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
                    MOVBAN_JOB.CHAVE_JOB = 22 AND
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
            COPLAS.ORDENS,
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
            APONTAMENTOS.CHAVE_ORDEM = ORDENS.CHAVE AND
            ORDENS.CHAVE_JOB = 22 AND
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

    return resultado


def contas_estrategicas_ano_mes_a_mes():
    """Totaliza o valor das contas estrategicas do periodo informado em site setup mes a mes"""
    site_setup = get_site_setup()
    if site_setup:
        data_ano_inicio = site_setup.atualizacoes_data_ano_inicio
        data_ano_fim = site_setup.atualizacoes_data_mes_fim

    relatorios = []
    plano_contas = [
        ('2.01.01.%', 'MERCADORIA_REVENDA'),
        ('2.03.%', 'IMPOSTOS'),
        ('2.01.02.%', 'MP'),
        ('3.02.03.%', 'ENERGIA'),
        ('3.03.%', 'SALARIOS_ENCARGOS'),
    ]

    for codigo_plano, descricao_plano in plano_contas:
        relatorio = get_relatorios_financeiros('pagar', coluna_mes_liquidacao=True, job=22,
                                               centro_resultado_coplas=True,
                                               data_liquidacao_inicio=data_ano_inicio,
                                               data_liquidacao_fim=data_ano_fim, plano_conta_codigo=codigo_plano)
        relatorio = completar_meses(pd.DataFrame(relatorio), 'MES_LIQUIDACAO')
        if 'VALOR_EFETIVO' not in relatorio.columns:  # type:ignore
            relatorio['VALOR_EFETIVO'] = 0  # type:ignore
        relatorio = relatorio.rename(columns={'VALOR_EFETIVO': descricao_plano})  # type:ignore

        relatorios.append(relatorio)

    resultado = pd.DataFrame()
    for relatorio in relatorios:
        if resultado.empty:
            resultado = pd.DataFrame(relatorio)
            continue
        resultado = pd.merge(resultado, relatorio, how='inner', on='MES_LIQUIDACAO')

    resultado = resultado.to_dict(orient='records')

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
            PRODUTOS.CHAVE_FAMILIA IN (7767, 7766, 8378, 12441) AND
            PRODUTOS_JOBS_CUSTOS.CHAVE_JOB IN (22, 25) AND
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

    return resultado


def migrar_regioes():
    mapeamento_destino_origem = {
        'nome': 'REGIAO',
    }

    origem = REGIOES.objects.all()
    if origem:
        destino = Regioes.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'nome': objeto_origem.REGIAO,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_estados():
    mapeamento_destino_origem = {
        'uf': 'ESTADO',
        'sigla': 'SIGLA',
        'regiao': ('CHAVE_REGIAO', ('chave_analysis', 'CHAVE')),
    }

    origem = ESTADOS.objects.all()
    if origem:
        destino = Estados.objects
        regiao = Regioes.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                fk_regiao = regiao.filter(chave_analysis=objeto_origem.CHAVE_REGIAO.CHAVE).first()  # type:ignore

                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'uf': objeto_origem.ESTADO,
                        'sigla': objeto_origem.SIGLA,
                        'regiao': fk_regiao,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_estados_icms():
    mapeamento_destino_origem = {
        'icms': 'ALIQUOTA',
    }

    origem = MATRIZ_ICMS.objects.all()
    if origem:
        destino = EstadosIcms.objects
        estados = Estados.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(
                uf_origem__chave_analysis=objeto_origem.UF_EMITENTE.pk,  # type:ignore
                uf_destino__chave_analysis=objeto_origem.UF_DESTINO.pk,  # type:ignore
            ).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                uf_origem_fk = estados.filter(chave_analysis=objeto_origem.UF_EMITENTE.pk).first()  # type:ignore
                uf_destino_fk = estados.filter(chave_analysis=objeto_origem.UF_DESTINO.pk).first()  # type:ignore

                instancia, criado = destino.update_or_create(
                    uf_origem__chave_analysis=objeto_origem.UF_EMITENTE.pk,  # type:ignore
                    uf_destino__chave_analysis=objeto_origem.UF_DESTINO.pk,  # type:ignore
                    defaults={
                        'uf_origem': uf_origem_fk,
                        'uf_destino': uf_destino_fk,
                        'icms': objeto_origem.ALIQUOTA,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_cidades():
    mapeamento_destino_origem = {
        'estado': ('UF', ('sigla', 'SIGLA')),
        'nome': 'CIDADE',
    }

    origem = FAIXAS_CEP.objects.all()
    if origem:
        destino = Cidades.objects
        estado = Estados.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                fk_estado = estado.filter(chave_analysis=objeto_origem.UF.CHAVE).first()  # type:ignore

                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'estado': fk_estado,
                        'nome': objeto_origem.CIDADE,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_unidades():
    mapeamento_destino_origem = {
        'unidade': 'UNIDADE',
        'descricao': 'DESCRICAO',
    }

    origem = UNIDADES.objects.all()
    if origem:
        destino = Unidades.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'unidade': objeto_origem.UNIDADE,
                        'descricao': objeto_origem.DESCRICAO,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_produtos():
    mapeamento_destino_origem = {
        'nome': 'CODIGO',
        'unidade': ('CHAVE_UNIDADE', ('chave_analysis', 'CHAVE')),
        'descricao': 'DESCRICAO',
        'peso_liquido': 'PESO_LIQUIDO',
        'peso_bruto': 'PESO_BRUTO',
        'ean13': 'CODIGO_BARRA',
    }

    origem = PRODUTOS.objects.filter(CHAVE_FAMILIA__CHAVE__in=(7766, 7767, 8378, 12441)).all()
    if origem:
        destino = Produtos.objects
        unidade = Unidades.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)
            status = 'ativo' if objeto_origem.FORA_DE_LINHA == 'NAO' else 'inativo'
            prioridade = Decimal(3)
            if 'ESTOQUE A' in objeto_origem.CARACTERISTICA2:  # type:ignore
                prioridade = Decimal(1)
            elif 'ESTOQUE B' in objeto_origem.CARACTERISTICA2:  # type:ignore
                prioridade = Decimal(2)
            elif 'ESTOQUE C' in objeto_origem.CARACTERISTICA2:  # type:ignore
                prioridade = Decimal(3)

            if not mudou:
                mudou = objeto_destino.status != status  # type:ignore

            if not mudou:
                mudou = objeto_destino.prioridade != prioridade  # type:ignore

            if mudou:
                fk_unidade = unidade.filter(chave_analysis=objeto_origem.CHAVE_UNIDADE.CHAVE).first()  # type:ignore

                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'unidade': fk_unidade,
                        'prioridade': prioridade,
                        'status': status,
                        'nome': objeto_origem.CODIGO,
                        'descricao': objeto_origem.DESCRICAO,
                        'peso_liquido': round(objeto_origem.PESO_LIQUIDO, 4),  # type:ignore
                        'peso_bruto': round(objeto_origem.PESO_BRUTO, 4),  # type:ignore
                        'ean13': objeto_origem.CODIGO_BARRA,
                    }
                )
                instancia.m3_volume = round(Decimal(instancia.m3_volume), 4)
                instancia.full_clean()
                instancia.save()


def migrar_canais_vendas():
    mapeamento_destino_origem = {
        'descricao': 'DESCRICAO',
    }

    origem = CANAIS_VENDA.objects.all()
    if origem:
        destino = CanaisVendas.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)

            if mudou:
                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'descricao': objeto_origem.DESCRICAO,
                    }
                )
                instancia.full_clean()
                instancia.save()


def migrar_vendedores():
    mapeamento_destino_origem = {
        'nome': 'NOMERED',
        'canal_venda': ('CHAVE_CANAL', ('chave_analysis', 'CHAVE')),
    }

    origem = VENDEDORES.objects.all()
    if origem:
        destino = Vendedores.objects
        canal_vendas = CanaisVendas.objects
        for objeto_origem in origem:
            objeto_destino = destino.filter(chave_analysis=objeto_origem.pk).first()

            mudou = campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem)
            status = 'ativo' if objeto_origem.INATIVO == 'NAO' else 'inativo'

            if not mudou:
                mudou = objeto_destino.status != status  # type:ignore

            if mudou:
                fk_canal_vendas = canal_vendas.filter(
                    chave_analysis=objeto_origem.CHAVE_CANAL.CHAVE).first()  # type:ignore

                instancia, criado = destino.update_or_create(
                    chave_analysis=objeto_origem.pk,
                    defaults={
                        'chave_analysis': objeto_origem.pk,
                        'nome': objeto_origem.NOMERED,
                        'canal_venda': fk_canal_vendas,
                        'status': status,
                    }
                )
                instancia.full_clean()
                instancia.save()


# TODO: trocar para get_relatorios_financeiros
def migrar_comissoes(data_inicio, data_fim):
    if data_fim:
        data_para_comissao = """
            RECEBER.DATAVENCIMENTO >= TO_DATE(:data_inicio,'YYYY-MM-DD') AND
            RECEBER.DATAVENCIMENTO <= TO_DATE(:data_fim,'YYYY-MM-DD')
        """
        data = data_para_comissao
    else:
        data_para_rescisao = "RECEBER.DATAVENCIMENTO >= TO_DATE(:data_inicio,'YYYY-MM-DD')"
        data = data_para_rescisao

    sql = """
        SELECT
            RECEBER.DATAVENCIMENTO,
            RECEBER.DATALIQUIDACAO,
            NOTAS.NF,
            CLIENTES.NOMERED AS CLIENTE,
            ESTADOS.SIGLA AS UF_CLIENTE,
            COALESCE(UF_ORDEM.UF_ORDEM, NOTAS.CLI_ENT_UF, ESTADOS.SIGLA) AS UF_ENTREGA,
            COALESCE(UF_ORDEM.CIDADE_ORDEM, NOTAS.CLI_ENT_CIDADE, CLIENTES.CIDADE) AS CIDADE_ENTREGA,
            NOTAS_ORCAMENTO.LOG_NOME_INCLUSAO AS LOG_INCLUSAO_ORCAMENTO,
            REPRE_CAD.NOMERED AS REPRESENTANTE_CLIENTE,
            REPRESENTANTES.NOMERED AS REPRESENTANTE_NOTA,
            SEGUNDO_REPRE_CAD.NOMERED AS SEGUNDO_REPRE_CLIENTE,
            SEGUNDO_REPRESENTANTE.NOMERED AS SEGUNDO_REPRE_NOTA,
            VENDEDORES.NOMERED AS CARTEIRA_CLIENTE,
            CASE NOTAS.ESPECIE WHEN 'S' THEN 'SAIDA' WHEN 'E' THEN 'ENTRADA' END AS ESPECIE,
            SUM(ROUND(NOTAS_ITENS.VALOR_MERCADORIAS / NOTAS.VALOR_TOTAL * (RECEBER.VALORTOTAL - (RECEBER.ABATIMENTOS_DEVOLUCOES + RECEBER.ABATIMENTOS_OUTROS + COALESCE(RECEBER.DESCONTOS, 0))), 2)) - COALESCE(FRETE_NO_ITEM.FRETE_NO_ITEM, 0) AS VALOR_MERCADORIAS_PARCELA,
            RECEBER.ABATIMENTOS_DEVOLUCOES + RECEBER.ABATIMENTOS_OUTROS + COALESCE(RECEBER.DESCONTOS, 0) AS ABATIMENTOS_TOTAIS,
            COALESCE(FRETE_NO_ITEM.FRETE_NO_ITEM, 0) AS FRETE_NO_ITEM,
            0 AS DIVISAO,
            0 AS ERRO,
            INFRA.CONTEUDO AS INFRA,
            CASE WHEN CLIENTES_TIPOS.DESCRICAO IN ('PRE-MOLDADO', 'POSTE') THEN 'PRE-MOLDADO / POSTE' END AS PREMOLDADO_POSTE,
            PC.CONTEUDO AS PC

        FROM
            (
                SELECT DISTINCT
                    NOTAS.CHAVE AS CHAVE_NOTA,
                    NOTAS.NF,
                    NOTAS.PARCELAS,
                    NOTAS.VALOR_FRETE_INCL_ITEM,
                    ROUND(NOTAS.VALOR_FRETE_INCL_ITEM / NOTAS.PARCELAS, 2) AS FRETE_NO_ITEM

                FROM
                    COPLAS.NOTAS,
                    COPLAS.RECEBER

                WHERE
                    NOTAS.CHAVE = RECEBER.CHAVE_NOTA AND

                    {data}
            ) FRETE_NO_ITEM,
            (SELECT DISTINCT CHAVE_CLIENTE, 'INFRA' AS CONTEUDO FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CHAVE_INFORMACAO = 8) INFRA,
            (SELECT DISTINCT CHAVE_CLIENTE, 'PC' AS CONTEUDO FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CHAVE_INFORMACAO = 23) PC,
            (SELECT DISTINCT NOTAS.CHAVE, ORCAMENTOS.LOG_NOME_INCLUSAO FROM COPLAS.ORCAMENTOS, COPLAS.PEDIDOS, COPLAS.NOTAS_ITENS, COPLAS.NOTAS WHERE NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA(+) AND NOTAS_ITENS.NUMPED = PEDIDOS.CHAVE(+) AND PEDIDOS.CHAVE_ORCAMENTO = ORCAMENTOS.CHAVE(+)) NOTAS_ORCAMENTO,
            (SELECT NOTAS_ORDEM.CHAVE AS CHAVE_NOTA, ESTADOS_ORDEM.SIGLA AS UF_ORDEM, CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM FROM COPLAS.ESTADOS ESTADOS_ORDEM, COPLAS.NOTAS NOTAS_ORDEM, COPLAS.CLIENTES CLIENTES_ORDEM WHERE NOTAS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE) UF_ORDEM,
            COPLAS.ESTADOS,
            COPLAS.VENDEDORES,
            COPLAS.VENDEDORES REPRESENTANTES,
            COPLAS.VENDEDORES REPRE_CAD,
            COPLAS.VENDEDORES SEGUNDO_REPRESENTANTE,
            COPLAS.VENDEDORES SEGUNDO_REPRE_CAD,
            COPLAS.NOTAS,
            COPLAS.NOTAS_ITENS,
            COPLAS.CLIENTES,
            COPLAS.PRODUTOS,
            COPLAS.RECEBER,
            COPLAS.CLIENTES_TIPOS

        WHERE
            NOTAS.CHAVE = FRETE_NO_ITEM.CHAVE_NOTA(+) AND
            CLIENTES.CHAVE_TIPO = CLIENTES_TIPOS.CHAVE AND
            CLIENTES.CODCLI = INFRA.CHAVE_CLIENTE(+) AND
            CLIENTES.CODCLI = PC.CHAVE_CLIENTE(+) AND
            NOTAS.CHAVE = RECEBER.CHAVE_NOTA AND
            NOTAS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD(+) AND
            NOTAS.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTE.CODVENDEDOR(+) AND
            CLIENTES.CHAVE_VENDEDOR2 = SEGUNDO_REPRE_CAD.CODVENDEDOR(+) AND
            NOTAS.CHAVE = UF_ORDEM.CHAVE_NOTA(+) AND
            NOTAS.CHAVE_VENDEDOR = REPRESENTANTES.CODVENDEDOR(+) AND
            CLIENTES.CODVEND = REPRE_CAD.CODVENDEDOR(+) AND
            NOTAS.CHAVE_CLIENTE = CLIENTES.CODCLI AND
            CLIENTES.UF = ESTADOS.CHAVE AND
            CLIENTES.CHAVE_VENDEDOR3 = VENDEDORES.CODVENDEDOR(+) AND
            NOTAS.CHAVE = NOTAS_ORCAMENTO.CHAVE(+) AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA(+) AND
            NOTAS.VALOR_COMERCIAL = 'SIM' AND
            (PRODUTOS.CHAVE_FAMILIA IN (7766, 7767, 8378, 12441) OR PRODUTOS.CPROD IS NULL) AND

            {data}

        GROUP BY
            RECEBER.DATAVENCIMENTO,
            RECEBER.DATALIQUIDACAO,
            NOTAS.NF,
            CLIENTES.NOMERED,
            ESTADOS.SIGLA,
            COALESCE(UF_ORDEM.UF_ORDEM, NOTAS.CLI_ENT_UF, ESTADOS.SIGLA),
            COALESCE(UF_ORDEM.CIDADE_ORDEM, NOTAS.CLI_ENT_CIDADE, CLIENTES.CIDADE),
            NOTAS_ORCAMENTO.LOG_NOME_INCLUSAO,
            VENDEDORES.NOMERED,
            SEGUNDO_REPRE_CAD.NOMERED,
            SEGUNDO_REPRE_CAD.NOME,
            REPRE_CAD.NOMERED,
            REPRESENTANTES.NOMERED,
            SEGUNDO_REPRESENTANTE.NOMERED,
            SEGUNDO_REPRESENTANTE.NOME,
            CASE NOTAS.ESPECIE WHEN 'S' THEN 'SAIDA' WHEN 'E' THEN 'ENTRADA' END,
            RECEBER.ABATIMENTOS_DEVOLUCOES + RECEBER.ABATIMENTOS_OUTROS + COALESCE(RECEBER.DESCONTOS, 0),
            FRETE_NO_ITEM.FRETE_NO_ITEM,
            INFRA.CONTEUDO,
            CASE WHEN CLIENTES_TIPOS.DESCRICAO IN ('PRE-MOLDADO', 'POSTE') THEN 'PRE-MOLDADO / POSTE' END,
            PC.CONTEUDO

        ORDER BY
            NOTAS.NF
    """

    sql = sql.format(data=data)

    kwargs = {}
    if data_fim:
        kwargs.update({'data_fim': data_fim})
    origem = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, **kwargs)

    if origem:
        Comissoes.objects.all().delete()

        estados = Estados.objects
        cidades = Cidades.objects
        vendedores = Vendedores.objects

        for objeto_origem in origem:

            # status = 'ativo' if objeto_origem.INATIVO == 'NAO' else 'inativo'

            fk_uf_cliente = None
            if objeto_origem['UF_CLIENTE']:
                fk_uf_cliente = estados.filter(sigla=objeto_origem['UF_CLIENTE']).first()

            fk_uf_entrega = None
            fk_cidade_entrega = None
            if objeto_origem['UF_ENTREGA']:
                fk_uf_entrega = estados.filter(sigla=objeto_origem['UF_ENTREGA']).first()
                if objeto_origem['CIDADE_ENTREGA']:
                    fk_cidade_entrega = cidades.filter(nome=objeto_origem['CIDADE_ENTREGA'],
                                                       estado=fk_uf_entrega).first()

            fk_representante_cliente = None
            if objeto_origem['REPRESENTANTE_CLIENTE']:
                fk_representante_cliente = vendedores.filter(nome=objeto_origem['REPRESENTANTE_CLIENTE']).first()

            fk_representante_nota = None
            if objeto_origem['REPRESENTANTE_NOTA']:
                fk_representante_nota = vendedores.filter(nome=objeto_origem['REPRESENTANTE_NOTA']).first()

            fk_segundo_representante_cliente = None
            if objeto_origem['SEGUNDO_REPRE_CLIENTE']:
                fk_segundo_representante_cliente = vendedores.filter(
                    nome=objeto_origem['SEGUNDO_REPRE_CLIENTE']).first()

            fk_segundo_representante_nota = None
            if objeto_origem['SEGUNDO_REPRE_NOTA']:
                fk_segundo_representante_nota = vendedores.filter(nome=objeto_origem['SEGUNDO_REPRE_NOTA']).first()

            fk_carteira_cliente = None
            if objeto_origem['CARTEIRA_CLIENTE']:
                fk_carteira_cliente = vendedores.filter(nome=objeto_origem['CARTEIRA_CLIENTE']).first()

            instancia = Comissoes(
                data_vencimento=objeto_origem['DATAVENCIMENTO'],
                data_liquidacao=objeto_origem['DATALIQUIDACAO'],
                nota_fiscal=objeto_origem['NF'],
                cliente=objeto_origem['CLIENTE'],
                uf_cliente=fk_uf_cliente,
                uf_entrega=fk_uf_entrega,
                cidade_entrega=fk_cidade_entrega,
                inclusao_orcamento=objeto_origem['LOG_INCLUSAO_ORCAMENTO'],
                representante_cliente=fk_representante_cliente,
                representante_nota=fk_representante_nota,
                segundo_representante_cliente=fk_segundo_representante_cliente,
                segundo_representante_nota=fk_segundo_representante_nota,
                carteira_cliente=fk_carteira_cliente,
                especie=objeto_origem['ESPECIE'],
                valor_mercadorias_parcelas=round(Decimal(objeto_origem['VALOR_MERCADORIAS_PARCELA']), 2),
                valor_mercadorias_parcelas_nao_dividido=round(Decimal(objeto_origem['VALOR_MERCADORIAS_PARCELA']), 2),
                abatimentos_totais=round(Decimal(objeto_origem['ABATIMENTOS_TOTAIS']), 2),
                frete_item=round(Decimal(objeto_origem['FRETE_NO_ITEM']), 2),
                divisao=False,
                erro=False,
                infra=True if objeto_origem['INFRA'] else False,
                premoldado_poste=True if objeto_origem['PREMOLDADO_POSTE'] else False,
                parede_concreto=True if objeto_origem['PC'] else False,
            )

            vendedores_divisao: list[Vendedores] = []

            # Conferencia Segundo Representante

            segundo_cliente_consultor_diferente_carteira = False
            if instancia.segundo_representante_cliente:
                if instancia.segundo_representante_cliente.canal_venda.descricao.upper() == 'CONSULTOR TECNICO':
                    if instancia.segundo_representante_cliente != instancia.carteira_cliente:
                        segundo_cliente_consultor_diferente_carteira = True
                        instancia.divisao = True
                        if instancia.segundo_representante_cliente not in vendedores_divisao:
                            vendedores_divisao.append(instancia.segundo_representante_cliente)

            segundo_nota_consultor_diferente_carteira = False
            if instancia.segundo_representante_nota:
                if instancia.segundo_representante_nota.canal_venda.descricao.upper() == 'CONSULTOR TECNICO':
                    if instancia.segundo_representante_nota != instancia.carteira_cliente:
                        segundo_nota_consultor_diferente_carteira = True
                        instancia.divisao = True
                        if instancia.segundo_representante_nota not in vendedores_divisao:
                            vendedores_divisao.append(instancia.segundo_representante_nota)

            if segundo_cliente_consultor_diferente_carteira and segundo_nota_consultor_diferente_carteira:
                if instancia.segundo_representante_cliente != instancia.segundo_representante_nota:
                    instancia.erro = True

            # Listar atendimentos da carteira, UF faturamento e UF entrega

            atendimentos_carteira = []
            if instancia.carteira_cliente:
                atendimentos_carteira = instancia.carteira_cliente.vendedoresregioes.all()  # type:ignore
                if atendimentos_carteira:
                    atendimentos_carteira = [atendimento.regiao for atendimento in atendimentos_carteira]

            vendedores_faturamento = []
            if instancia.uf_cliente:
                vendedores_regioes_faturamento = instancia.uf_cliente.regiao.vendedoresregioes.all()  # type:ignore
                if vendedores_regioes_faturamento:
                    vendedores_faturamento = [regiao.vendedor for regiao in vendedores_regioes_faturamento]
                    if instancia.segundo_representante_cliente in vendedores_faturamento or \
                            instancia.segundo_representante_nota in vendedores_faturamento:
                        vendedores_faturamento = []

            vendedores_entrega = []
            if instancia.uf_entrega:
                vendedores_regioes_entrega = instancia.uf_entrega.regiao.vendedoresregioes.all()  # type:ignore
                if vendedores_regioes_entrega:
                    vendedores_entrega = [regiao.vendedor for regiao in vendedores_regioes_entrega]
                    if instancia.segundo_representante_cliente in vendedores_entrega or \
                            instancia.segundo_representante_nota in vendedores_entrega:
                        vendedores_entrega = []

            # Conferencia da carteira, UF faturamento e UF entrega

            if vendedores_faturamento and atendimentos_carteira:
                if instancia.carteira_cliente not in vendedores_faturamento:
                    instancia.divisao = True
                    for vendedor in vendedores_faturamento:
                        if vendedor not in vendedores_divisao and 'EOLICA' not in vendedor.nome:
                            vendedores_divisao.append(vendedor)

            if vendedores_entrega and atendimentos_carteira:
                if instancia.carteira_cliente not in vendedores_entrega:
                    instancia.divisao = True
                    for vendedor in vendedores_entrega:
                        if vendedor not in vendedores_divisao and 'EOLICA' not in vendedor.nome:
                            vendedores_divisao.append(vendedor)

            if not instancia.carteira_cliente:
                instancia.erro = True
            else:
                if instancia.carteira_cliente.canal_venda.descricao.upper() != 'CONSULTOR TECNICO':
                    instancia.erro = True

            divisoes = len(vendedores_divisao)
            if divisoes:
                instancia.valor_mercadorias_parcelas = round(instancia.valor_mercadorias_parcelas / 2, 2)

            instancia.full_clean()
            instancia.save()

            for vendedor in vendedores_divisao:
                instancia_divisao = ComissoesVendedores(
                    comissao=instancia,
                    vendedor=vendedor,
                )
                instancia_divisao.full_clean()
                instancia_divisao.save()

                instancia_dividida = Comissoes(
                    data_vencimento=instancia.data_vencimento,
                    data_liquidacao=instancia.data_liquidacao,
                    nota_fiscal=instancia.nota_fiscal,
                    cliente=instancia.cliente,
                    uf_cliente=instancia.uf_cliente,
                    uf_entrega=instancia.uf_entrega,
                    cidade_entrega=instancia.cidade_entrega,
                    inclusao_orcamento=instancia.inclusao_orcamento,
                    representante_cliente=instancia.representante_cliente,
                    representante_nota=instancia.representante_nota,
                    segundo_representante_cliente=instancia.segundo_representante_cliente,
                    segundo_representante_nota=instancia.carteira_cliente,
                    carteira_cliente=vendedor,
                    especie=instancia.especie,
                    valor_mercadorias_parcelas=round(instancia.valor_mercadorias_parcelas / divisoes, 2),
                    valor_mercadorias_parcelas_nao_dividido=instancia.valor_mercadorias_parcelas_nao_dividido,
                    abatimentos_totais=instancia.abatimentos_totais,
                    frete_item=instancia.frete_item,
                    divisao=instancia.divisao,
                    erro=instancia.erro,
                    infra=instancia.infra,
                    premoldado_poste=instancia.premoldado_poste,
                    parede_concreto=instancia.parede_concreto,
                )
                instancia_dividida.full_clean()
                instancia_dividida.save()


def migrar_faturamentos(data_inicio, data_fim):
    from dashboards.services import get_relatorios_vendas

    origem = get_relatorios_vendas('faturamentos', inicio=data_inicio, fim=data_fim, coluna_data_emissao=True,
                                   coluna_documento=True, coluna_cliente=True, coluna_estado=True,
                                   coluna_estado_destino=True, coluna_carteira=True, coluna_parcelas=True,
                                   coluna_log_nome_inclusao_orcamento=True, coluna_representante=True,
                                   coluna_representante_documento=True, coluna_segundo_representante=True,
                                   coluna_segundo_representante_documento=True, coluna_especie=True,
                                   coluna_status_documento=True, coluna_tipo_cliente=True,
                                   coluna_informacao_estrategica=True,
                                   familia_produto=[7766, 7767, 8378, 12441])

    infra = get_relatorios_vendas('faturamentos', inicio=data_inicio, fim=data_fim, coluna_documento=True,
                                  informacao_estrategica=8)
    infra = pd.DataFrame(infra)
    infra = infra[['DOCUMENTO']]
    infra['INFRA'] = 'INFRA'

    parede_concreto = get_relatorios_vendas('faturamentos', inicio=data_inicio, fim=data_fim, coluna_documento=True,
                                            informacao_estrategica=23)
    parede_concreto = pd.DataFrame(parede_concreto)
    parede_concreto = parede_concreto[['DOCUMENTO']]
    parede_concreto['PC'] = 'PC'

    origem = pd.DataFrame(origem)
    origem['DIVISAO'] = 0
    origem['ERRO'] = 0
    origem = pd.merge(origem, infra, how='left', on='DOCUMENTO').fillna('')
    origem = pd.merge(origem, parede_concreto, how='left', on='DOCUMENTO').fillna('')
    origem.loc[(origem['TIPO_CLIENTE'] != 'POSTE') & (origem['TIPO_CLIENTE'] != 'PRE-MOLDADO'), 'TIPO_CLIENTE'] = ''

    origem = origem.rename(columns={
        'DOCUMENTO': 'NF',
        'STATUS_DOCUMENTO': 'STATUS',
        'REPRESENTANTE': 'REPRESENTANTE_CLIENTE',
        'REPRESENTANTE_DOCUMENTO': 'REPRESENTANTE_NOTA',
        'SEGUNDO_REPRESENTANTE': 'SEGUNDO_REPRE_CLIENTE',
        'SEGUNDO_REPRESENTANTE_DOCUMENTO': 'SEGUNDO_REPRE_NOTA',
        'CARTEIRA': 'CARTEIRA_CLIENTE',
        'UF_PRINCIPAL': 'UF_CLIENTE',
        'UF_DESTINO': 'UF_ENTREGA',
        'TIPO_CLIENTE': 'PREMOLDADO_POSTE',
    })
    origem = origem[['DATA_EMISSAO', 'NF', 'PARCELAS', 'CLIENTE', 'UF_CLIENTE', 'UF_ENTREGA', 'LOG_INCLUSAO_ORCAMENTO',
                     'REPRESENTANTE_CLIENTE', 'REPRESENTANTE_NOTA', 'SEGUNDO_REPRE_CLIENTE', 'SEGUNDO_REPRE_NOTA',
                     'CARTEIRA_CLIENTE', 'ESPECIE', 'STATUS', 'VALOR_MERCADORIAS', 'DIVISAO', 'ERRO', 'INFRA',
                     'PREMOLDADO_POSTE', 'PC',]]

    origem = origem.to_dict(orient='records')

    if origem:
        Faturamentos.objects.all().delete()

        estados = Estados.objects
        vendedores = Vendedores.objects
        representante_coplas = Vendedores.objects.get(nome='COPLAS')

        for objeto_origem in origem:

            fk_uf_cliente = None
            if objeto_origem['UF_CLIENTE']:
                fk_uf_cliente = estados.filter(sigla=objeto_origem['UF_CLIENTE']).first()

            fk_uf_entrega = None
            if objeto_origem['UF_ENTREGA']:
                fk_uf_entrega = estados.filter(sigla=objeto_origem['UF_ENTREGA']).first()

            fk_representante_cliente = None
            if objeto_origem['REPRESENTANTE_CLIENTE']:
                fk_representante_cliente = vendedores.filter(nome=objeto_origem['REPRESENTANTE_CLIENTE']).first()

            fk_representante_nota = None
            if objeto_origem['REPRESENTANTE_NOTA']:
                fk_representante_nota = vendedores.filter(nome=objeto_origem['REPRESENTANTE_NOTA']).first()

            fk_segundo_representante_cliente = None
            if objeto_origem['SEGUNDO_REPRE_CLIENTE']:
                fk_segundo_representante_cliente = vendedores.filter(
                    nome=objeto_origem['SEGUNDO_REPRE_CLIENTE']).first()

            fk_segundo_representante_nota = None
            if objeto_origem['SEGUNDO_REPRE_NOTA']:
                fk_segundo_representante_nota = vendedores.filter(nome=objeto_origem['SEGUNDO_REPRE_NOTA']).first()

            fk_carteira_cliente = None
            if objeto_origem['CARTEIRA_CLIENTE']:
                fk_carteira_cliente = vendedores.filter(nome=objeto_origem['CARTEIRA_CLIENTE']).first()

            instancia = Faturamentos(
                data_emissao=objeto_origem['DATA_EMISSAO'],
                nota_fiscal=objeto_origem['NF'],
                parcelas=objeto_origem['PARCELAS'],
                cliente=objeto_origem['CLIENTE'],
                uf_cliente=fk_uf_cliente,
                uf_entrega=fk_uf_entrega,
                inclusao_orcamento=objeto_origem['LOG_INCLUSAO_ORCAMENTO'],
                representante_cliente=fk_representante_cliente,
                representante_nota=fk_representante_nota,
                segundo_representante_cliente=fk_segundo_representante_cliente,
                segundo_representante_nota=fk_segundo_representante_nota,
                carteira_cliente=fk_carteira_cliente,
                especie=objeto_origem['ESPECIE'],
                status=objeto_origem['STATUS'],
                valor_mercadorias=round(Decimal(objeto_origem['VALOR_MERCADORIAS']), 2),
                valor_mercadorias_nao_dividido=round(Decimal(objeto_origem['VALOR_MERCADORIAS']), 2),
                divisao=False,
                erro=False,
                infra=True if objeto_origem['INFRA'] else False,
                premoldado_poste=True if objeto_origem['PREMOLDADO_POSTE'] else False,
                parede_concreto=True if objeto_origem['PC'] else False,
            )

            vendedores_divisao: list[Vendedores] = []

            # Conferencia Segundo Representante

            segundo_cliente_diferente_representante = False
            if instancia.segundo_representante_cliente:
                if instancia.segundo_representante_cliente.canal_venda.descricao.upper() == 'REPRESENTANTE':
                    if instancia.segundo_representante_cliente != instancia.representante_cliente:
                        segundo_cliente_diferente_representante = True
                        instancia.divisao = True
                        if instancia.segundo_representante_cliente not in vendedores_divisao:
                            vendedores_divisao.append(instancia.segundo_representante_cliente)

            segundo_nota_diferente_representante = False
            if instancia.segundo_representante_nota:
                if instancia.segundo_representante_nota.canal_venda.descricao.upper() == 'REPRESENTANTE':
                    if instancia.segundo_representante_nota != instancia.representante_nota:
                        segundo_nota_diferente_representante = True
                        instancia.divisao = True
                        if instancia.segundo_representante_nota not in vendedores_divisao:
                            vendedores_divisao.append(instancia.segundo_representante_nota)

            if segundo_cliente_diferente_representante and segundo_nota_diferente_representante:
                if instancia.segundo_representante_cliente != instancia.segundo_representante_nota:
                    instancia.erro = True

            # Listar atendimentos do representante

            atendimentos_representante = []
            if instancia.representante_nota:
                atendimentos_representante = instancia.representante_nota.vendedoresestados.all()  # type:ignore
                if atendimentos_representante:
                    atendimentos_representante = [atendimento.estado for atendimento in atendimentos_representante]

            # Conferencia do representante, UF faturamento e UF entrega

            if atendimentos_representante:
                if instancia.uf_cliente not in atendimentos_representante or \
                        instancia.uf_entrega not in atendimentos_representante:
                    instancia.divisao = True
                    if representante_coplas not in vendedores_divisao:
                        vendedores_divisao.append(representante_coplas)

            if not instancia.representante_nota:
                instancia.erro = True
            else:
                if instancia.representante_nota.canal_venda.descricao.upper() not in ('REPRESENTANTE', 'MERCADO LIVRE'):
                    instancia.erro = True
                if instancia.representante_nota != instancia.representante_cliente:
                    instancia.erro = True

            divisoes = len(vendedores_divisao)
            if divisoes:
                instancia.valor_mercadorias = round(instancia.valor_mercadorias / 2, 2)

            instancia.full_clean()
            instancia.save()

            for vendedor in vendedores_divisao:
                instancia_divisao = FaturamentosVendedores(
                    faturamento=instancia,
                    vendedor=vendedor,
                )
                instancia_divisao.full_clean()
                instancia_divisao.save()

                instancia_dividida = Faturamentos(
                    data_emissao=instancia.data_emissao,
                    nota_fiscal=instancia.nota_fiscal,
                    parcelas=instancia.parcelas,
                    cliente=instancia.cliente,
                    uf_cliente=instancia.uf_cliente,
                    uf_entrega=instancia.uf_entrega,
                    inclusao_orcamento=instancia.inclusao_orcamento,
                    representante_cliente=instancia.representante_cliente,
                    representante_nota=vendedor,
                    segundo_representante_cliente=instancia.segundo_representante_cliente,
                    segundo_representante_nota=instancia.representante_nota,
                    carteira_cliente=instancia.carteira_cliente,
                    especie=instancia.especie,
                    status=instancia.status,
                    valor_mercadorias=round(instancia.valor_mercadorias / divisoes, 2),
                    valor_mercadorias_nao_dividido=instancia.valor_mercadorias_nao_dividido,
                    divisao=instancia.divisao,
                    erro=instancia.erro,
                    infra=instancia.infra,
                    premoldado_poste=instancia.premoldado_poste,
                    parede_concreto=instancia.parede_concreto,
                )
                instancia_dividida.full_clean()
                instancia_dividida.save()


def sugestoes_modelos(modelos: Iterable, tags: Iterable):
    """Retorna uma lista de tuplas com o modelo e a quantidade de insidencias do modelo, basedo nos iteraveis de modelos e tags"""
    sugestoes = []
    for tag in tags:
        modelos_com_tag = ProdutosModelos.objects.filter(
            tags=tag).exclude(pk__in=[modelo.pk for modelo in modelos])  # type:ignore
        [sugestoes.append(modelo) for modelo in modelos_com_tag]
    sugestoes_contagem = Counter(sugestoes).most_common()
    return sugestoes_contagem
