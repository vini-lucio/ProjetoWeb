from utils.custom import DefaultDict
from utils.oracle.conectar import executar_oracle
from utils.lfrete import pedidos as lfrete_pedidos
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import (get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda,
                              get_transportadoras, get_consultores_tecnicos_ativos)
from utils.lfrete import notas as lfrete_notas, orcamentos as lfrete_orcamentos
from utils.perdidos_justificativas import justificativas
from frete.services import get_dados_pedidos_em_aberto, get_transportadoras_valores_atendimento
from home.services import frete_cif_ano_mes_a_mes, faturado_bruto_ano_mes_a_mes
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
import pandas as pd


class DashBoardVendas():
    def __init__(self) -> None:
        self.SITE_SETUP = get_site_setup()
        if self.SITE_SETUP:
            self.META_DIARIA = self.SITE_SETUP.meta_diaria_as_float
            self.META_MES = self.SITE_SETUP.meta_mes_as_float
            self.PRIMEIRO_DIA_MES = self.SITE_SETUP.primeiro_dia_mes_as_ddmmyyyy
            self.PRIMEIRO_DIA_UTIL_MES = self.SITE_SETUP.primeiro_dia_util_mes_as_ddmmyyyy
            self.ULTIMO_DIA_MES = self.SITE_SETUP.ultimo_dia_mes_as_ddmmyyyy
            self.PRIMEIRO_DIA_UTIL_PROXIMO_MES = self.SITE_SETUP.primeiro_dia_util_proximo_mes_as_ddmmyyyy
            self.DESPESA_ADMINISTRATIVA_FIXA = self.SITE_SETUP.despesa_administrativa_fixa_as_float

        self.PEDIDOS_DIA, self.TONELADAS_DIA, self.RENTABILIDADE_PEDIDOS_DIA = rentabilidade_pedidos_dia(
            self.DESPESA_ADMINISTRATIVA_FIXA,
            self.PRIMEIRO_DIA_UTIL_PROXIMO_MES
        )
        self.PORCENTAGEM_META_DIA = int(self.PEDIDOS_DIA / self.META_DIARIA * 100)
        self.FALTAM_META_DIA = round(self.META_DIARIA - self.PEDIDOS_DIA, 2)
        self.CONVERSAO_DE_ORCAMENTOS = conversao_de_orcamentos()
        self.FALTAM_ABRIR_ORCAMENTOS_DIA = round(self.FALTAM_META_DIA / (self.CONVERSAO_DE_ORCAMENTOS / 100), 2)
        self.RENTABILIDADE_PEDIDOS_MES = rentabilidade_pedidos_mes(self.DESPESA_ADMINISTRATIVA_FIXA,
                                                                   self.PRIMEIRO_DIA_MES,
                                                                   self.PRIMEIRO_DIA_UTIL_MES,
                                                                   self.ULTIMO_DIA_MES,
                                                                   self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.RENTABILIDADE_PEDIDOS_MES_MC_MES = self.RENTABILIDADE_PEDIDOS_MES['mc_mes']
        self.RENTABILIDADE_PEDIDOS_MES_TOTAL_MES = self.RENTABILIDADE_PEDIDOS_MES['total_mes']
        self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE = self.RENTABILIDADE_PEDIDOS_MES['rentabilidade_mes']
        self.TONELADAS_MES = self.RENTABILIDADE_PEDIDOS_MES['toneladas_mes']
        self.PEDIDOS_MES = self.RENTABILIDADE_PEDIDOS_MES['total_mes']
        self.PORCENTAGEM_META_MES = int(self.PEDIDOS_MES / self.META_MES * 100)
        self.FALTAM_META_MES = round(self.META_MES - self.PEDIDOS_MES, 2)
        self.COR_RENTABILIDADE_PEDIDOS_DIA = cor_rentabilidade_css(self.RENTABILIDADE_PEDIDOS_DIA)
        self.COR_RENTABILIDADE_PEDIDOS_MES = cor_rentabilidade_css(self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE)

        self.FALTA_MUDAR_COR_MES = falta_mudar_cor_mes(self.RENTABILIDADE_PEDIDOS_MES_MC_MES,
                                                       self.RENTABILIDADE_PEDIDOS_MES_TOTAL_MES,
                                                       self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE)
        self.FALTA_MUDAR_COR_MES_VALOR = round(self.FALTA_MUDAR_COR_MES[0], 2)
        self.FALTA_MUDAR_COR_MES_VALOR_RENTABILIDADE = round(self.FALTA_MUDAR_COR_MES[1], 2)
        self.FALTA_MUDAR_COR_MES_PORCENTAGEM = round(self.FALTA_MUDAR_COR_MES[2], 2)
        self.FALTA_MUDAR_COR_MES_COR = self.FALTA_MUDAR_COR_MES[3]

        self.DATA_HORA_ATUAL = data_hora_atual()

        self.CONFERE_PEDIDOS = confere_pedidos()

    def get_dados(self):
        dados = {
            'meta_diaria': self.META_DIARIA,
            'pedidos_dia': self.PEDIDOS_DIA,
            'toneladas_dia': self.TONELADAS_DIA,
            'porcentagem_meta_dia': self.PORCENTAGEM_META_DIA,
            'faltam_meta_dia': self.FALTAM_META_DIA,
            'conversao_de_orcamentos': self.CONVERSAO_DE_ORCAMENTOS,
            'faltam_abrir_orcamentos_dia': self.FALTAM_ABRIR_ORCAMENTOS_DIA,
            'meta_mes': self.META_MES,
            'pedidos_mes': self.PEDIDOS_MES,
            'toneladas_mes': self.TONELADAS_MES,
            'porcentagem_meta_mes': self.PORCENTAGEM_META_MES,
            'faltam_meta_mes': self.FALTAM_META_MES,
            'data_hora_atual': self.DATA_HORA_ATUAL,
            'rentabilidade_pedidos_dia': self.RENTABILIDADE_PEDIDOS_DIA,
            'cor_rentabilidade_css_dia': self.COR_RENTABILIDADE_PEDIDOS_DIA,
            'rentabilidade_pedidos_mes_rentabilidade_mes': self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE,
            'cor_rentabilidade_css_mes': self.COR_RENTABILIDADE_PEDIDOS_MES,
            'falta_mudar_cor_mes_valor': self.FALTA_MUDAR_COR_MES_VALOR,
            'falta_mudar_cor_mes_valor_rentabilidade': self.FALTA_MUDAR_COR_MES_VALOR_RENTABILIDADE,
            'falta_mudar_cor_mes_porcentagem': self.FALTA_MUDAR_COR_MES_PORCENTAGEM,
            'falta_mudar_cor_mes_cor': self.FALTA_MUDAR_COR_MES_COR,
            'confere_pedidos': self.CONFERE_PEDIDOS,
        }
        return dados


class DashboardVendasTv(DashBoardVendas):
    def __init__(self) -> None:
        super().__init__()
        self.ASSISTENTES_TECNICOS = get_assistentes_tecnicos()
        self.AGENDA_VEC = get_assistentes_tecnicos_agenda()

    def get_dados(self):
        dados = super().get_dados()
        dados.update({
            'assistentes_tecnicos': self.ASSISTENTES_TECNICOS,
            'agenda_vec': self.AGENDA_VEC,
        })
        return dados


class DashboardVendasSupervisao(DashBoardVendas):
    def __init__(self) -> None:
        super().__init__()

        faturado_bruto = faturado_bruto_ano_mes_a_mes(mes_atual=True)
        try:
            faturado_bruto = faturado_bruto['FATURADO_TOTAL']  # type:ignore
        except TypeError:
            faturado_bruto = 0

        frete_cif = frete_cif_ano_mes_a_mes(mes_atual=True)
        try:
            frete_cif = frete_cif['AGILLI'] + frete_cif['OUTRAS_TRANSPORTADORAS']  # type:ignore
        except TypeError:
            frete_cif = 0
        frete_cif = 0 if faturado_bruto == 0 else frete_cif / faturado_bruto * 100

        self.FRETE_CIF = frete_cif
        self.CARTEIRAS_MES = []
        for carteira in get_consultores_tecnicos_ativos():
            RENTABILIDADE_PEDIDOS_MES = rentabilidade_pedidos_mes(self.DESPESA_ADMINISTRATIVA_FIXA,
                                                                  self.PRIMEIRO_DIA_MES,
                                                                  self.PRIMEIRO_DIA_UTIL_MES,
                                                                  self.ULTIMO_DIA_MES,
                                                                  self.PRIMEIRO_DIA_UTIL_PROXIMO_MES, carteira.nome)
            RENTABILIDADE_PEDIDOS_MES_MC_MES = RENTABILIDADE_PEDIDOS_MES['mc_mes']
            RENTABILIDADE_PEDIDOS_MES_TOTAL_MES = RENTABILIDADE_PEDIDOS_MES['total_mes']
            RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE = RENTABILIDADE_PEDIDOS_MES['rentabilidade_mes']
            TONELADAS_MES = RENTABILIDADE_PEDIDOS_MES['toneladas_mes']
            COR_RENTABILIDADE_PEDIDOS_MES = cor_rentabilidade_css(RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE)
            meta_mes_float = float(carteira.meta_mes)
            dados_carteira = {
                'carteira': carteira.nome,
                'mc_mes_carteira': RENTABILIDADE_PEDIDOS_MES_MC_MES,
                'meta_mes': meta_mes_float,
                'total_mes_carteira': RENTABILIDADE_PEDIDOS_MES_TOTAL_MES,
                'falta_meta': meta_mes_float - RENTABILIDADE_PEDIDOS_MES_TOTAL_MES,
                'porcentagem_meta_mes': 0 if meta_mes_float == 0 else int(RENTABILIDADE_PEDIDOS_MES_TOTAL_MES / meta_mes_float * 100),
                'rentabilidade_mes_carteira': RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE,
                'toneladas_mes_carteira': TONELADAS_MES,
                'cor_rentabilidade_mes_carteira': COR_RENTABILIDADE_PEDIDOS_MES,
            }
            self.CARTEIRAS_MES.append(dados_carteira)

    def get_dados(self):
        dados = super().get_dados()
        dados.update({
            'carteiras_mes': self.CARTEIRAS_MES,
            'frete_cif': self.FRETE_CIF,
        })
        return dados


def carteira_mapping(carteira):
    carteira_actions_mapping = {
        'PREMOLDADO / POSTE': {
            'carteira': "%%",
            'filtro_nao_carteira': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND"
        },
        'PAREDE DE CONCRETO': {
            'carteira': "%%",
            'filtro_nao_carteira': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND"
        }
    }

    filtro_nao_carteira = ""
    if carteira in carteira_actions_mapping:
        filtro_nao_carteira = carteira_actions_mapping[carteira]['filtro_nao_carteira']
        carteira = carteira_actions_mapping[carteira]['carteira']

    return carteira, filtro_nao_carteira


def rentabilidade_pedidos_dia(despesa_administrativa_fixa: float, primeiro_dia_util_proximo_mes: str,
                              carteira: str = '%%') -> tuple[float, float, float]:
    """Valor mercadorias, toneladas de produto proprio e rentabilidade dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
    carteira, filtro_nao_carteira = carteira_mapping(carteira)

    sql = """
        SELECT
            -- despesa administrativa (ultima subtração)
            TOTAL_MES_MOEDA,
            TONELADAS_PROPRIO,
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - :despesa_administrativa_fixa AS RENTABILIDADE

        FROM
            (
                SELECT
                    ROUND(LFRETE.MC_SEM_FRETE / (SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM))) * 100, 2) AS RENTABILIDADE,
                    ROUND(LFRETE.MC_SEM_FRETE, 2) AS MC_MES,
                    -- Sem conversão de moeda
                    ROUND(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 2) AS TOTAL_MES,
                    ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END), 2) AS TOTAL_MES_MOEDA,
                    COALESCE(ROUND(NVL(LFRETE.MC_SEM_FRETE_PP / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2), 0) AS RENTABILIDADE_PP,
                    ROUND(LFRETE.MC_SEM_FRETE_PP, 2) AS MC_MES_PP,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PP,
                    COALESCE(ROUND(NVL(LFRETE.MC_SEM_FRETE_PT / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2), 0) AS RENTABILIDADE_PT,
                    ROUND(LFRETE.MC_SEM_FRETE_PT, 2) AS MC_MES_PT,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PT,
                    COALESCE(ROUND(NVL(LFRETE.MC_SEM_FRETE_PQ / (NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END), 0)), 0) * 100, 2), 0) AS RENTABILIDADE_PQ,
                    ROUND(LFRETE.MC_SEM_FRETE_PQ, 2) AS MC_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 2) AS TOTAL_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.PESO_LIQUIDO ELSE 0 END) / 1000, 3) AS TONELADAS_PROPRIO

                FROM
                    (
                        SELECT
                            ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

                        FROM
                            (
                                {lfrete} AND

                                    -- place holder para selecionar carteira
                                    VENDEDORES.NOMERED LIKE :carteira AND
                                    {filtro_nao_carteira}

                                    -- hoje
                                    PEDIDOS.DATA_PEDIDO = TRUNC(SYSDATE) AND
                                    -- primeiro dia util do proximo mes
                                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
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

                    -- place holder para selecionar carteira
                    VENDEDORES.NOMERED LIKE :carteira AND
                    {filtro_nao_carteira}

                    -- hoje
                    PEDIDOS.DATA_PEDIDO = TRUNC(SYSDATE) AND
                    -- primeiro dia util do proximo mes
                    PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')

                GROUP BY
                    LFRETE.MC_SEM_FRETE,
                    LFRETE.MC_SEM_FRETE_PP,
                    LFRETE.MC_SEM_FRETE_PT,
                    LFRETE.MC_SEM_FRETE_PQ
            )
    """

    sql = sql.format(lfrete=lfrete_pedidos, filtro_nao_carteira=filtro_nao_carteira)

    resultado = executar_oracle(sql, despesa_administrativa_fixa=despesa_administrativa_fixa,
                                primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes, carteira=carteira)

    # não consegui identificar o porque, não esta retornado [(none,),] e sim [], indice [0][0] não funciona
    if not resultado:
        return 0.00, 0.00, 0.00,

    return float(resultado[0][0]), float(resultado[0][1]), float(resultado[0][2]),


def conversao_de_orcamentos(carteira: str = '%%'):
    """Taxa de conversão de orçamentos com valor comercial dos ultimos 90 dias, ignorando orçamentos oportunidade e palavras chave de erros internos"""
    carteira, filtro_nao_carteira = carteira_mapping(carteira)

    justificativas_itens = justificativas(False)
    justificativas_itens_excluidos = justificativas(True)

    sql = """
        SELECT
            ROUND(SUM(CONVERSAO.FECHADO) / SUM(CONVERSAO.TOTAL) * 100, 2) AS CONVERSAO

        FROM
            (
                SELECT
                    ROUND(SUM(CASE WHEN ORCAMENTOS_ITENS.STATUS='FECHADO' THEN (ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END ELSE 0 END), 2) AS FECHADO,
                    ROUND(SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END), 2) AS TOTAL

                FROM
                    COPLAS.ORCAMENTOS,
                    COPLAS.ORCAMENTOS_ITENS,
                    COPLAS.CLIENTES,
                    COPLAS.VENDEDORES

                WHERE
                    CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
                    VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                    ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
                    ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                    ORCAMENTOS.DATA_PEDIDO >= SYSDATE - 90 AND

                    VENDEDORES.NOMERED LIKE :carteira AND
                    {filtro_nao_carteira}

                    {justificativas_itens}

                UNION ALL

                SELECT
                    0 AS FECHADO,
                    ROUND(SUM(ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA * ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE), 2) AS TOTAL

                FROM
                    COPLAS.ORCAMENTOS,
                    COPLAS.ORCAMENTOS_ITENS_EXCLUIDOS,
                    COPLAS.CLIENTES,
                    COPLAS.VENDEDORES

                WHERE
                    CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
                    VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                    ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_ORCAMENTO AND
                    ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                    ORCAMENTOS.DATA_PEDIDO >= SYSDATE - 90 AND

                    VENDEDORES.NOMERED LIKE :carteira AND
                    {filtro_nao_carteira}

                    {justificativas_itens_excluidos}
            ) CONVERSAO
    """

    sql = sql.format(filtro_nao_carteira=filtro_nao_carteira,
                     justificativas_itens=justificativas_itens,
                     justificativas_itens_excluidos=justificativas_itens_excluidos)

    resultado = executar_oracle(sql, carteira=carteira)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def rentabilidade_pedidos_mes(despesa_administrativa_fixa: float, primeiro_dia_mes: str,
                              primeiro_dia_util_mes: str, ultimo_dia_mes: str,
                              primeiro_dia_util_proximo_mes: str, carteira: str = '%%') -> dict[str, float]:
    """Valor mercadorias, toneladas de produto proprio e rentabilidade dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes"""
    carteira, filtro_nao_carteira = carteira_mapping(carteira)

    sql = """
        SELECT
            ROUND((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100), 2) AS MC_MES,
            TOTAL_MES_MOEDA,

            -- despesa administrativa (ultima subtração)
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - :despesa_administrativa_fixa AS RENTABILIDADE,
            TONELADAS_PROPRIO

        FROM
            (
                SELECT
                    ROUND((LFRETE.MC_SEM_FRETE + DEVOLUCOES.RENTABILIDADE) / (SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) + DEVOLUCOES.TOTAL) * 100, 2) AS RENTABILIDADE,
                    ROUND(LFRETE.MC_SEM_FRETE + DEVOLUCOES.RENTABILIDADE, 2) AS MC_MES,
                    -- Total sem converter moeda
                    ROUND(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) + DEVOLUCOES.TOTAL, 2) AS TOTAL_MES,
                    ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END) + DEVOLUCOES.TOTAL, 2) AS TOTAL_MES_MOEDA,
                    COALESCE(ROUND((LFRETE.MC_SEM_FRETE_PP + DEVOLUCOES.RENTABILIDADE_PP) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PP) * 100, 2), 0) AS RENTABILIDADE_PP,
                    ROUND(LFRETE.MC_SEM_FRETE_PP + DEVOLUCOES.RENTABILIDADE_PP, 2) AS MC_MES_PP,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PP, 2) AS TOTAL_MES_PP,
                    COALESCE(ROUND((LFRETE.MC_SEM_FRETE_PT + DEVOLUCOES.RENTABILIDADE_PT) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PT) * 100, 2), 0) AS RENTABILIDADE_PT,
                    ROUND(LFRETE.MC_SEM_FRETE_PT + DEVOLUCOES.RENTABILIDADE_PT, 2) AS MC_MES_PT,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PT, 2) AS TOTAL_MES_PT,
                    COALESCE(ROUND((LFRETE.MC_SEM_FRETE_PQ + DEVOLUCOES.RENTABILIDADE_PQ) / (SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) END) + DEVOLUCOES.PQ) * 100, 2), 0) AS RENTABILIDADE_PQ,
                    ROUND(LFRETE.MC_SEM_FRETE_PQ + DEVOLUCOES.RENTABILIDADE_PQ, 2) AS MC_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN (PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) ELSE 0 END) + DEVOLUCOES.PQ, 2) AS TOTAL_MES_PQ,
                    ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.PESO_LIQUIDO ELSE 0 END) / 1000, 3) AS TONELADAS_PROPRIO

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

                            -- place holder para selecionar carteira
                            VENDEDORES.NOMERED LIKE :carteira AND
                            {filtro_nao_carteira}

                            -- primeiro dia do mes
                            NOTAS.DATA_EMISSAO >= TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                            -- ultimo dia do mes
                            NOTAS.DATA_EMISSAO <= TO_DATE(:ultimo_dia_mes,'DD-MM-YYYY')
                    ) DEVOLUCOES,
                    (
                        SELECT
                            ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                            ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

                        FROM
                            (
                                {lfrete} AND

                                    -- place holder para selecionar carteira
                                    VENDEDORES.NOMERED LIKE :carteira AND
                                    {filtro_nao_carteira}

                                    (
                                        (
                                            -- primeiro dia do mes
                                            PEDIDOS.DATA_PEDIDO < TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                                            -- primeiro dia util do mes
                                            PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE(:primeiro_dia_util_mes,'DD-MM-YYYY') AND
                                            -- primeiro dia util do proximo mes
                                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
                                        ) OR
                                        (
                                            -- primeiro dia do mes
                                            PEDIDOS.DATA_PEDIDO >= TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                                            -- ultimo dia do mes
                                            PEDIDOS.DATA_PEDIDO <= TO_DATE(:ultimo_dia_mes,'DD-MM-YYYY') AND
                                            -- primeiro dia util do proximo mes
                                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
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

                    -- place holder para selecionar carteira
                    VENDEDORES.NOMERED LIKE :carteira AND
                    {filtro_nao_carteira}

                    (
                        (
                            -- primeiro dia do mes
                            PEDIDOS.DATA_PEDIDO < TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                            -- primeiro dia util do mes
                            PEDIDOS_ITENS.DATA_ENTREGA > TO_DATE(:primeiro_dia_util_mes,'DD-MM-YYYY') AND
                            -- primeiro dia util do proximo mes
                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
                        ) OR
                        (
                            -- primeiro dia do mes
                            PEDIDOS.DATA_PEDIDO >= TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                            -- ultimo dia do mes
                            PEDIDOS.DATA_PEDIDO <= TO_DATE(:ultimo_dia_mes,'DD-MM-YYYY') AND
                            -- primeiro dia util do proximo mes
                            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
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

    sql = sql.format(lfrete=lfrete_pedidos, filtro_nao_carteira=filtro_nao_carteira)

    resultado = executar_oracle(sql, despesa_administrativa_fixa=despesa_administrativa_fixa,
                                primeiro_dia_mes=primeiro_dia_mes, primeiro_dia_util_mes=primeiro_dia_util_mes,
                                ultimo_dia_mes=ultimo_dia_mes,
                                primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes, carteira=carteira)

    if not resultado:
        dicionario = {
            'mc_mes': 0.0,
            'total_mes': 0.0,
            'rentabilidade_mes': 0.0,
            'toneladas_mes': 0.0,
        }

        return dicionario

    mc_mes = 0.0 if not resultado[0][0] else resultado[0][0]
    total_mes = 0.0 if not resultado[0][1] else resultado[0][1]
    rentabilidade_mes = 0.0 if not resultado[0][2] else resultado[0][2]
    toneladas_mes = 0.0 if not resultado[0][3] else resultado[0][3]

    dicionario = {
        'mc_mes': float(mc_mes),
        'total_mes': float(total_mes),
        'rentabilidade_mes': float(rentabilidade_mes),
        'toneladas_mes': float(toneladas_mes),
    }

    return dicionario


def confere_pedidos(carteira: str = '%%') -> list | None:
    """Confere possiveis erros dos pedidos em aberto (seleção armazenada no ID 2186)"""
    sql = "SELECT SELECAO FROM COPLAS.SELECOES WHERE CHAVE = 2186"

    sql = executar_oracle(sql)
    sql = sql[0][0]

    resultado = executar_oracle(sql, exportar_cabecalho=True, carteira=carteira)

    erros_atendimento_transportadoras = confere_pedidos_atendimento_transportadoras()
    if erros_atendimento_transportadoras:
        for erro_atendiemto_transportadoras in erros_atendimento_transportadoras:
            resultado.append(erro_atendiemto_transportadoras)

    if not resultado:
        return []

    return resultado


def confere_pedidos_atendimento_transportadoras() -> list | None:
    dados_pedidos = get_dados_pedidos_em_aberto()
    transportadoras = get_transportadoras()
    erros = []

    if not dados_pedidos:
        return []

    for dados_pedido in dados_pedidos:
        try:
            get_transportadoras_valores_atendimento(dados_orcamento_pedido=dados_pedido,
                                                    transportadora_orcamento_pedido=True)
        except ObjectDoesNotExist:
            transportadora = transportadoras.filter(chave_analysis=dados_pedido['CHAVE_TRANSPORTADORA'])
            if transportadora:
                pedido = dados_pedido['PEDIDO']
                consultor = dados_pedido['CARTEIRA']
                erro = 'TRANSPORTADORA NÃO ATENDE O DESTINO'
                erros.append({'PEDIDO': pedido, 'CONSULTOR': consultor, 'ERRO': erro})

    return erros


def map_relatorio_vendas_sql_string_placeholders(orcamento: bool, trocar_para_itens_excluidos: bool = False, **kwargs_formulario):
    """
        SQLs estão em um dict onde a chave é o nome do campo do formulario e o valor é um dict com o placeholder como
        chave e o codigo sql como valor
    """
    notas_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    notas_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE), 0), 2) AS MC_VALOR"
    notas_lfrete_from = """
        (
            SELECT
                CHAVE_NOTA_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL), 2) AS MC_SEM_FRETE

            FROM
                (
                    {lfrete_notas} AND

                        NOTAS.DATA_EMISSAO >= :data_inicio AND
                        NOTAS.DATA_EMISSAO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_NOTA_ITEM
        ) LFRETE,
    """.format(lfrete_notas=lfrete_notas)
    notas_lfrete_join = "LFRETE.CHAVE_NOTA_ITEM = NOTAS_ITENS.CHAVE AND"

    map_sql_notas_base = {
        'valor_mercadorias': "SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM, 0), 0))) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': """
            (
                SELECT
                    NOTAS_ITENS.CHAVE_NOTA,
                    SUM(NOTAS_ITENS.PESO_LIQUIDO) AS PESO_LIQUIDO

                FROM
                    COPLAS.NOTAS_ITENS

                GROUP BY
                    NOTAS_ITENS.CHAVE_NOTA
            ) NOTAS_PESO_LIQUIDO,
        """,

        'fonte_itens': "COPLAS.NOTAS_ITENS,",

        'fonte': "COPLAS.NOTAS,",

        'fonte_joins': """
            PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
            NOTAS.CHAVE = NOTAS_PESO_LIQUIDO.CHAVE_NOTA(+) AND
        """,

        'fonte_where': "NOTAS.VALOR_COMERCIAL = 'SIM' AND",

        'fonte_where_data': """
            NOTAS.DATA_EMISSAO >= :data_inicio AND
            NOTAS.DATA_EMISSAO <= :data_fim
        """,
    }

    map_sql_notas = {
        'coluna_media_dia': {'media_dia_campo_alias': "SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM, 0), 0))) / COUNT(DISTINCT NOTAS.DATA_EMISSAO) AS MEDIA_DIA,", },

        'coluna_data_emissao': {'data_emissao_campo_alias': "NOTAS.DATA_EMISSAO,",
                                'data_emissao_campo': "NOTAS.DATA_EMISSAO,", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY||MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY||MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },

        'coluna_tipo_cliente': {'tipo_cliente_campo_alias': "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,",
                                'tipo_cliente_campo': "CLIENTES_TIPOS.DESCRICAO,", },
        'tipo_cliente': {'tipo_cliente_pesquisa': "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND", },

        'coluna_familia_produto': {'familia_produto_campo_alias': "FAMILIA_PRODUTOS.FAMILIA AS FAMILIA_PRODUTO,",
                                   'familia_produto_campo': "FAMILIA_PRODUTOS.FAMILIA,", },
        'familia_produto': {'familia_produto_pesquisa': "FAMILIA_PRODUTOS.CHAVE = :chave_familia_produto AND", },

        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(NOTAS_ITENS.PRECO_TABELA) AS PRECO_TABELA_INCLUSAO,",
                                         'preco_tabela_inclusao_campo': "MAX(NOTAS_ITENS.PRECO_TABELA),", },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(NOTAS_ITENS.PRECO_FATURADO), 2) AS PRECO_VENDA_MEDIO,",
                                     'preco_venda_medio_campo': "ROUND(AVG(NOTAS_ITENS.PRECO_FATURADO), 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(NOTAS_ITENS.QUANTIDADE) AS QUANTIDADE,",
                              'quantidade_campo': "SUM(NOTAS_ITENS.QUANTIDADE),", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': """
            CLIENTES.STATUS != 'X' AND
            NOT EXISTS(
                SELECT DISTINCT
                    CLIENTES.CHAVE_GRUPOECONOMICO

                FROM
                    COPLAS.CLIENTES,
                    COPLAS.NOTAS

                WHERE
                    CLIENTES.CHAVE_GRUPOECONOMICO = GRUPO_ECONOMICO.CHAVE AND
                    CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
                    NOTAS.VALOR_COMERCIAL = 'SIM' AND

                    NOTAS.DATA_EMISSAO > :data_fim
            ) AND
            NOT EXISTS(
                SELECT DISTINCT
                    ORCAMENTOS.CHAVE_CLIENTE

                FROM
                    COPLAS.ORCAMENTOS

                WHERE
                    ORCAMENTOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND
                    ORCAMENTOS.STATUS = 'EM ABERTO' AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO'
            ) AND
        """, },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "", },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT NOTAS.NF) AS QUANTIDADE_DOCUMENTOS,",
                                         'quantidade_documentos_campo': "COUNT(DISTINCT NOTAS.NF),", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "",
                                            'status_produto_orcamento_campo': "", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "",
                                                 'status_produto_orcamento_tipo_campo': "",
                                                 'status_produto_orcamento_tipo_from': "",
                                                 'status_produto_orcamento_tipo_join': "", },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "",
                                          'status_produto_orcamento_tipo_from': "",
                                          'status_produto_orcamento_tipo_join': "", },

        'coluna_rentabilidade': {'lfrete_coluna': notas_lfrete_coluna,
                                 'lfrete_valor_coluna': notas_lfrete_valor_coluna,
                                 'lfrete_from': notas_lfrete_from,
                                 'lfrete_join': notas_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': notas_lfrete_coluna,
                                       'lfrete_valor_coluna': notas_lfrete_valor_coluna,
                                       'lfrete_from': notas_lfrete_from,
                                       'lfrete_join': notas_lfrete_join, },
    }

    orcamentos_status_produto_orcamento_tipo_from = "COPLAS.STATUS_ORCAMENTOS_ITENS,"
    orcamentos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS.STATUS AND"

    orcamentos_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    orcamentos_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END), 0), 2) AS MC_VALOR"
    orcamentos_lfrete_from = """
        (
            SELECT
                CHAVE_ORCAMENTO_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL), 2) AS MC_SEM_FRETE

            FROM
                (
                    {lfrete_orcamentos} AND

                        ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                        ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
                        ORCAMENTOS.DATA_PEDIDO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_ORCAMENTO_ITEM
        ) LFRETE,
    """.format(lfrete_orcamentos=lfrete_orcamentos)
    orcamentos_lfrete_join = "LFRETE.CHAVE_ORCAMENTO_ITEM = ORCAMENTOS_ITENS.CHAVE AND"

    map_sql_orcamentos_base = {
        'valor_mercadorias': "SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0), 0))) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': "",

        'fonte_itens': "COPLAS.ORCAMENTOS_ITENS,",

        'fonte': "COPLAS.ORCAMENTOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = ORCAMENTOS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
        """,

        'fonte_where': """
            ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
            ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
        """,

        'fonte_where_data': """
            ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
            ORCAMENTOS.DATA_PEDIDO <= :data_fim
        """,
    }

    map_sql_orcamentos = {
        'coluna_media_dia': {'media_dia_campo_alias': "SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0), 0))) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END) / COUNT(DISTINCT ORCAMENTOS.DATA_PEDIDO) AS MEDIA_DIA,"},

        'coluna_data_emissao': {'data_emissao_campo_alias': "ORCAMENTOS.DATA_PEDIDO AS DATA_EMISSAO,",
                                'data_emissao_campo': "ORCAMENTOS.DATA_PEDIDO,", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY||MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY||MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },

        'coluna_tipo_cliente': {'tipo_cliente_campo_alias': "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,",
                                'tipo_cliente_campo': "CLIENTES_TIPOS.DESCRICAO,", },
        'tipo_cliente': {'tipo_cliente_pesquisa': "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND", },

        'coluna_familia_produto': {'familia_produto_campo_alias': "FAMILIA_PRODUTOS.FAMILIA AS FAMILIA_PRODUTO,",
                                   'familia_produto_campo': "FAMILIA_PRODUTOS.FAMILIA,", },
        'familia_produto': {'familia_produto_pesquisa': "FAMILIA_PRODUTOS.CHAVE = :chave_familia_produto AND", },

        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(ORCAMENTOS_ITENS.PRECO_TABELA) AS PRECO_TABELA_INCLUSAO,",
                                         'preco_tabela_inclusao_campo': "MAX(ORCAMENTOS_ITENS.PRECO_TABELA),", },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(ORCAMENTOS_ITENS.PRECO_VENDA), 2) AS PRECO_VENDA_MEDIO,",
                                     'preco_venda_medio_campo': "ROUND(AVG(ORCAMENTOS_ITENS.PRECO_VENDA), 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(ORCAMENTOS_ITENS.QUANTIDADE) AS QUANTIDADE,",
                              'quantidade_campo': "SUM(ORCAMENTOS_ITENS.QUANTIDADE),", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': "", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "{} AND".format(justificativas(False)), },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT ORCAMENTOS.NUMPED) AS QUANTIDADE_DOCUMENTOS,",
                                         'quantidade_documentos_campo': "COUNT(DISTINCT ORCAMENTOS.NUMPED),", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "ORCAMENTOS_ITENS.STATUS,",
                                            'status_produto_orcamento_campo': "ORCAMENTOS_ITENS.STATUS,", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "ORCAMENTOS_ITENS.STATUS = :chave_status_produto_orcamento AND", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "STATUS_ORCAMENTOS_ITENS.TIPO AS STATUS_TIPO,",
                                                 'status_produto_orcamento_tipo_campo': "STATUS_ORCAMENTOS_ITENS.TIPO,",
                                                 'status_produto_orcamento_tipo_from': orcamentos_status_produto_orcamento_tipo_from,
                                                 'status_produto_orcamento_tipo_join': orcamentos_status_produto_orcamento_tipo_join, },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "STATUS_ORCAMENTOS_ITENS.TIPO = :status_produto_orcamento_tipo AND" if kwargs_formulario.get('status_produto_orcamento_tipo') != "PERDIDO_CANCELADO" else "STATUS_ORCAMENTOS_ITENS.TIPO IN ('PERDIDO', 'CANCELADO') AND",
                                          'status_produto_orcamento_tipo_from': orcamentos_status_produto_orcamento_tipo_from,
                                          'status_produto_orcamento_tipo_join': orcamentos_status_produto_orcamento_tipo_join, },

        'coluna_rentabilidade': {'lfrete_coluna': orcamentos_lfrete_coluna,
                                 'lfrete_valor_coluna': orcamentos_lfrete_valor_coluna,
                                 'lfrete_from': orcamentos_lfrete_from,
                                 'lfrete_join': orcamentos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': orcamentos_lfrete_coluna,
                                       'lfrete_valor_coluna': orcamentos_lfrete_valor_coluna,
                                       'lfrete_from': orcamentos_lfrete_from,
                                       'lfrete_join': orcamentos_lfrete_join, },
    }

    # Itens de orçamento excluidos somente o que difere de orçamento

    orcamentos_itens_excluidos_status_produto_orcamento_tipo_from = orcamentos_status_produto_orcamento_tipo_from
    orcamentos_itens_excluidos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS_EXCLUIDOS.STATUS AND"

    orcamentos_itens_excluidos_lfrete_coluna = ", 0 AS MC"
    orcamentos_itens_excluidos_lfrete_valor_coluna = ", 0 AS MC_VALOR"
    orcamentos_itens_excluidos_lfrete_from = ""
    orcamentos_itens_excluidos_lfrete_join = ""

    map_sql_orcamentos_base_itens_excluidos = {
        'valor_mercadorias': "SUM((ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE * ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END) AS VALOR_MERCADORIAS",

        'fonte_itens': "COPLAS.ORCAMENTOS_ITENS_EXCLUIDOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_ORCAMENTO AND
        """,
    }

    map_sql_orcamentos_itens_excluidos = {
        # TODO: calcular na junção de orçamentos e itens excluidos?
        'coluna_media_dia': {'media_dia_campo_alias': "0 AS MEDIA_DIA,"},

        # TODO: calcular na junção de orçamentos e itens excluidos?
        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "0 AS PRECO_TABELA_INCLUSAO,",
                                         'preco_tabela_inclusao_campo': "", },

        # TODO: calcular na junção de orçamentos e itens excluidos?
        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "0 AS PRECO_VENDA_MEDIO,",
                                     'preco_venda_medio_campo': "", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE) AS QUANTIDADE,",
                              'quantidade_campo': "SUM(ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE),", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "{} AND".format(justificativas(True)), },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "0 AS QUANTIDADE_DOCUMENTOS,",
                                         'quantidade_documentos_campo': "", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS,",
                                            'status_produto_orcamento_campo': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS,", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS = :chave_status_produto_orcamento AND", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "STATUS_ORCAMENTOS_ITENS.TIPO AS STATUS_TIPO,",
                                                 'status_produto_orcamento_tipo_campo': "STATUS_ORCAMENTOS_ITENS.TIPO,",
                                                 'status_produto_orcamento_tipo_from': orcamentos_itens_excluidos_status_produto_orcamento_tipo_from,
                                                 'status_produto_orcamento_tipo_join': orcamentos_itens_excluidos_status_produto_orcamento_tipo_join, },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "STATUS_ORCAMENTOS_ITENS.TIPO = :status_produto_orcamento_tipo AND" if kwargs_formulario.get('status_produto_orcamento_tipo') != "PERDIDO_CANCELADO" else "STATUS_ORCAMENTOS_ITENS.TIPO IN ('PERDIDO', 'CANCELADO') AND",
                                          'status_produto_orcamento_tipo_from': orcamentos_itens_excluidos_status_produto_orcamento_tipo_from,
                                          'status_produto_orcamento_tipo_join': orcamentos_itens_excluidos_status_produto_orcamento_tipo_join, },

        'coluna_rentabilidade': {'lfrete_coluna': orcamentos_itens_excluidos_lfrete_coluna,
                                 'lfrete_valor_coluna': orcamentos_itens_excluidos_lfrete_valor_coluna,
                                 'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                 'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': orcamentos_itens_excluidos_lfrete_coluna,
                                       'lfrete_valor_coluna': orcamentos_itens_excluidos_lfrete_valor_coluna,
                                       'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                       'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },
    }

    sql_final = {}
    if orcamento:
        sql_final.update(map_sql_orcamentos_base)
        if trocar_para_itens_excluidos:
            sql_final.update(map_sql_orcamentos_base_itens_excluidos)
    else:
        sql_final.update(map_sql_notas_base)

    for chave, valor in kwargs_formulario.items():
        if valor:
            if orcamento:
                get_map_orcamento = map_sql_orcamentos.get(chave)
                if get_map_orcamento:
                    sql_final.update(get_map_orcamento)  # type:ignore
                    if trocar_para_itens_excluidos:
                        get_map_orcamento_itens_excluidos = map_sql_orcamentos_itens_excluidos.get(chave)
                        if get_map_orcamento_itens_excluidos:
                            sql_final.update(get_map_orcamento_itens_excluidos)  # type:ignore
            else:
                get_map_nota = map_sql_notas.get(chave)
                if get_map_nota:
                    sql_final.update(get_map_nota)  # type:ignore

    return sql_final


def get_relatorios_vendas(orcamento: bool, **kwargs):
    # TODO: forçar somente usuarios do grupo de supervisao ou direito especifico
    # TODO: coluna de cada mes? cada ano?
    kwargs_sql = {}
    kwargs_sql_itens_excluidos = {}
    kwargs_ora = {}

    data_inicio = kwargs.get('inicio')
    data_fim = kwargs.get('fim')
    grupo_economico = kwargs.get('grupo_economico')
    carteira = kwargs.get('carteira')
    tipo_cliente = kwargs.get('tipo_cliente')
    familia_produto = kwargs.get('familia_produto')
    produto = kwargs.get('produto')
    cidade = kwargs.get('cidade')
    estado = kwargs.get('estado')
    status_produto_orcamento = kwargs.get('status_produto_orcamento')
    status_produto_orcamento_tipo = kwargs.get('status_produto_orcamento_tipo')
    trocar_para_itens_excluidos = kwargs.pop('considerar_itens_excluidos', False)

    if not data_inicio:
        data_inicio = datetime.date(datetime(2010, 1, 1))

    if not data_fim:
        data_fim = datetime.date(datetime(2999, 12, 31))

    kwargs_sql.update(map_relatorio_vendas_sql_string_placeholders(orcamento, **kwargs))
    if trocar_para_itens_excluidos:
        kwargs_sql_itens_excluidos.update(map_relatorio_vendas_sql_string_placeholders(
            orcamento, trocar_para_itens_excluidos, **kwargs))  # type:ignore

    # kwargs_ora precisa conter os placeholders corretamente

    if grupo_economico:
        kwargs_ora.update({'grupo_economico': grupo_economico, })

    if carteira:
        chave_carteira = carteira.pk
        kwargs_ora.update({'chave_carteira': chave_carteira, })

    if tipo_cliente:
        chave_tipo_cliente = tipo_cliente.pk
        kwargs_ora.update({'chave_tipo_cliente': chave_tipo_cliente, })

    if familia_produto:
        chave_familia_produto = familia_produto.pk
        kwargs_ora.update({'chave_familia_produto': chave_familia_produto, })

    if produto:
        kwargs_ora.update({'produto': produto, })

    if cidade:
        kwargs_ora.update({'cidade': cidade, })

    if estado:
        chave_estado = estado.pk
        kwargs_ora.update({'chave_estado': chave_estado, })

    if status_produto_orcamento:
        if orcamento:
            chave_status_produto_orcamento = status_produto_orcamento.DESCRICAO
            kwargs_ora.update({'chave_status_produto_orcamento': chave_status_produto_orcamento, })

    if status_produto_orcamento_tipo:
        if orcamento:
            if status_produto_orcamento_tipo != "PERDIDO_CANCELADO":
                kwargs_ora.update({'status_produto_orcamento_tipo': status_produto_orcamento_tipo, })

    sql_base = """
        SELECT
            {data_emissao_campo_alias}
            {ano_mes_emissao_campo_alias}
            {ano_emissao_campo_alias}
            {mes_emissao_campo_alias}
            {carteira_campo_alias}
            {grupo_economico_campo_alias}
            {quantidade_documentos_campo_alias}
            {cidade_campo_alias}
            {estado_campo_alias}
            {tipo_cliente_campo_alias}
            {familia_produto_campo_alias}
            {produto_campo_alias}
            {unidade_campo_alias}
            {status_produto_orcamento_campo_alias}
            {status_produto_orcamento_tipo_campo_alias}
            {preco_tabela_inclusao_campo_alias}
            {preco_venda_medio_campo_alias}
            {quantidade_campo_alias}
            {media_dia_campo_alias}

            {valor_mercadorias}

            {lfrete_coluna}
            {lfrete_valor_coluna}

        FROM
            {lfrete_from}
            {notas_peso_liquido_from}
            {status_produto_orcamento_tipo_from}
            COPLAS.VENDEDORES,
            {fonte_itens}
            {fonte}
            COPLAS.FAMILIA_PRODUTOS,
            COPLAS.PRODUTOS,
            COPLAS.UNIDADES,
            COPLAS.GRUPO_ECONOMICO,
            COPLAS.CLIENTES,
            COPLAS.CLIENTES_TIPOS,
            COPLAS.ESTADOS

        WHERE
            {lfrete_join}
            {status_produto_orcamento_tipo_join}
            PRODUTOS.CHAVE_UNIDADE = UNIDADES.CHAVE AND
            FAMILIA_PRODUTOS.CHAVE = PRODUTOS.CHAVE_FAMILIA AND
            CLIENTES.UF = ESTADOS.CHAVE AND
            {fonte_joins}
            CLIENTES.CHAVE_TIPO = CLIENTES_TIPOS.CHAVE AND
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES.CHAVE_GRUPOECONOMICO = GRUPO_ECONOMICO.CHAVE(+) AND
            {fonte_where}

            {grupo_economico_pesquisa}
            {carteira_pesquisa}
            {tipo_cliente_pesquisa}
            {familia_produto_pesquisa}
            {produto_pesquisa}
            {cidade_pesquisa}
            {estado_pesquisa}
            {nao_compraram_depois_pesquisa}
            {status_produto_orcamento_pesquisa}
            {status_produto_orcamento_tipo_pesquisa}
            {desconsiderar_justificativa_pesquisa}

            {fonte_where_data}

        GROUP BY
            {data_emissao_campo}
            {ano_mes_emissao_campo}
            {ano_emissao_campo}
            {mes_emissao_campo}
            {carteira_campo}
            {grupo_economico_campo}
            {tipo_cliente_campo}
            {familia_produto_campo}
            {produto_campo}
            {unidade_campo}
            {status_produto_orcamento_campo}
            {status_produto_orcamento_tipo_campo}
            {cidade_campo}
            {estado_campo}
            1

        ORDER BY
            {ano_mes_emissao_campo}
            {ano_emissao_campo}
            {mes_emissao_campo}
            {carteira_campo}
            {tipo_cliente_campo}
            {familia_produto_campo}
            {proporcao_campo}
            {produto_campo}
            {status_produto_orcamento_campo}
            {status_produto_orcamento_tipo_campo}
            VALOR_MERCADORIAS DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, data_fim=data_fim, **kwargs_ora)

    if trocar_para_itens_excluidos:
        sql_itens_excluidos = sql_base.format_map(DefaultDict(kwargs_sql_itens_excluidos))
        resultado_itens_excluidos = executar_oracle(sql_itens_excluidos, exportar_cabecalho=True,
                                                    data_inicio=data_inicio, data_fim=data_fim, **kwargs_ora)

        dt_resultado = pd.DataFrame(resultado)
        dt_resultado_itens_excluidos = pd.DataFrame(resultado_itens_excluidos)

        dt_resultado_final = pd.concat([dt_resultado, dt_resultado_itens_excluidos])

        alias_para_header_groupby = ['DATA_EMISSAO', 'ANO_EMISSAO', 'MES_EMISSAO', 'CHAVE_GRUPO_ECONOMICO',
                                     'GRUPO', 'CARTEIRA', 'TIPO_CLIENTE', 'FAMILIA_PRODUTO', 'PRODUTO', 'UNIDADE',
                                     'CIDADE_PRINCIPAL', 'UF_PRINCIPAL', 'STATUS', 'STATUS_TIPO',]
        # Em caso de não ser só soma para juntar os dataframes com sum(), usar em caso the agg()
        # alias_para_header_agg = {'VALOR_MERCADORIAS': 'sum', 'MC': 'sum', 'MC_VALOR': 'sum', 'MEDIA_DIA': 'sum',
        #                          'PRECO_TABELA_INCLUSAO': 'sum', 'PRECO_VENDA_MEDIO': 'sum', 'QUANTIDADE': 'sum',
        #                          'QUANTIDADE_DOCUMENTOS': 'sum', }
        cabecalhos = list(dt_resultado_final.columns)

        alias_para_header_groupby = [header for header in alias_para_header_groupby if header in cabecalhos]
        # Em caso de não ser só soma para juntar os dataframes com sum(), usar em caso the agg()
        # alias_para_header_agg = {key: value for key, value in alias_para_header_agg.items() if key in cabecalhos}

        if alias_para_header_groupby:
            dt_resultado_final = dt_resultado_final.groupby(alias_para_header_groupby).sum().reset_index()
            resultado = dt_resultado_final.to_dict(orient='records')
        else:
            dt_resultado_final = dt_resultado_final.sum()
            resultado = [dt_resultado_final.to_dict()]

    return resultado


def get_email_contatos(condicao):
    sql = """
        SELECT DISTINCT
            RTRIM(LTRIM(CONTATOS.EMAIL)) AS EMAIL

        FROM
            COPLAS.CONTATOS,
            COPLAS.CLIENTES

        WHERE
            CLIENTES.CODCLI = CONTATOS.CHAVE_CLIENTE AND

            {condicao} AND

            CONTATOS.ATIVO = 'SIM' AND
            CONTATOS.ENVIAR_MALA = 'SIM' AND
            CLIENTES.STATUS IN ('Y', 'P') AND
            CONTATOS.CHAVE NOT IN (
                SELECT
                    CHAVE

                FROM
                    COPLAS.CONTATOS

                WHERE
                    EMAIL LIKE '% %' OR
                    EMAIL NOT LIKE '%_@_%' OR
                    EMAIL LIKE '%,%' OR
                    EMAIL LIKE '%>%' OR
                    EMAIL LIKE '%<%' OR
                    EMAIL LIKE '.%' OR
                    EMAIL LIKE '%.' OR
                    EMAIL LIKE '%..%' OR
                    EMAIL LIKE '%"%' OR
                    EMAIL LIKE '%(%' OR
                    EMAIL LIKE '%)%' OR
                    EMAIL LIKE '%;%' OR
                    EMAIL LIKE '%\\%' OR
                    EMAIL LIKE '%[%' OR
                    EMAIL LIKE '%]%' OR
                    EMAIL LIKE '%!%' OR
                    EMAIL LIKE '%#%' OR
                    EMAIL LIKE '%$%' OR
                    EMAIL LIKE '%*%' OR
                    EMAIL LIKE '%/%' OR
                    EMAIL LIKE '%?%' OR
                    EMAIL LIKE '%{{%' OR
                    EMAIL LIKE '%}}%' OR
                    EMAIL LIKE '%|%' OR
                    EMAIL IS NULL
            )

        ORDER BY
            EMAIL
    """

    sql = sql.format(condicao=condicao)

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    return resultado
