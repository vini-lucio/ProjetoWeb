from typing import Literal
from utils.custom import DefaultDict
from utils.oracle.conectar import executar_oracle
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import (get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda,
                              get_transportadoras, get_consultores_tecnicos_ativos)
from utils.lfrete import notas as lfrete_notas, orcamentos as lfrete_orcamentos, pedidos as lfrete_pedidos
from utils.perdidos_justificativas import justificativas
from frete.services import get_dados_pedidos_em_aberto, get_transportadoras_valores_atendimento
from home.services import frete_cif_ano_mes_a_mes, faturado_bruto_ano_mes_a_mes
from home.models import Vendedores
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
import pandas as pd


# TODO: incluir coluna da rentabilidade real sem subtrair pela despesa adm
class DashBoardVendas():
    def __init__(self, carteira='%%') -> None:
        self.carteira = carteira
        self.site_setup = get_site_setup()
        if self.site_setup:
            self.dias_meta = self.site_setup.dias_uteis_mes_as_float
            self.primeiro_dia_mes = self.site_setup.primeiro_dia_mes_as_ddmmyyyy
            self.primeiro_dia_util_mes = self.site_setup.primeiro_dia_util_mes_as_ddmmyyyy
            self.ultimo_dia_mes = self.site_setup.ultimo_dia_mes_as_ddmmyyyy
            self.primeiro_dia_util_proximo_mes = self.site_setup.primeiro_dia_util_proximo_mes_as_ddmmyyyy
            self.despesa_administrativa_fixa = self.site_setup.despesa_administrativa_fixa_as_float

            if self.carteira == '%%':
                self.meta_diaria = self.site_setup.meta_diaria_as_float
                self.meta_mes = self.site_setup.meta_mes_as_float
            else:
                vendedor = Vendedores.objects.get(nome=self.carteira)
                self.meta_mes = float(vendedor.meta_mes)
                self.meta_diaria = self.meta_mes / self.dias_meta

        self.pedidos_dia, self.toneladas_dia, self.rentabilidade_pedidos_dia = rentabilidade_pedidos_dia(
            self.despesa_administrativa_fixa, self.primeiro_dia_util_proximo_mes, self.carteira)
        self.porcentagem_mc_dia = self.rentabilidade_pedidos_dia + self.despesa_administrativa_fixa
        self.porcentagem_meta_dia = int(self.pedidos_dia / self.meta_diaria * 100) if self.meta_diaria else 0
        self.faltam_meta_dia = round(self.meta_diaria - self.pedidos_dia, 2)
        self.conversao_de_orcamentos = conversao_de_orcamentos(self.carteira)
        self.faltam_abrir_orcamentos_dia = round(
            self.faltam_meta_dia / (self.conversao_de_orcamentos / 100), 2) if self.conversao_de_orcamentos else 0.0
        self.rentabilidade_pedidos_mes = rentabilidade_pedidos_mes(self.despesa_administrativa_fixa,
                                                                   self.primeiro_dia_mes, self.primeiro_dia_util_mes,
                                                                   self.ultimo_dia_mes,
                                                                   self.primeiro_dia_util_proximo_mes, self.carteira)
        self.rentabilidade_pedidos_mes_mc_mes = self.rentabilidade_pedidos_mes['mc_mes']
        self.rentabilidade_pedidos_mes_total_mes = self.rentabilidade_pedidos_mes['total_mes']
        self.rentabilidade_pedidos_mes_rentabilidade = self.rentabilidade_pedidos_mes['rentabilidade_mes']
        self.toneladas_mes = self.rentabilidade_pedidos_mes['toneladas_mes']
        self.pedidos_mes = self.rentabilidade_pedidos_mes['total_mes']
        self.porcentagem_mc_mes = self.rentabilidade_pedidos_mes_rentabilidade + self.despesa_administrativa_fixa
        self.porcentagem_meta_mes = int(self.pedidos_mes / self.meta_mes * 100) if self.meta_mes else 0
        self.faltam_meta_mes = round(self.meta_mes - self.pedidos_mes, 2)
        self.cor_rentabilidade_pedidos_dia = cor_rentabilidade_css(self.rentabilidade_pedidos_dia)
        self.cor_rentabilidade_pedidos_mes = cor_rentabilidade_css(self.rentabilidade_pedidos_mes_rentabilidade)

        self.falta_mudar_cor_mes = falta_mudar_cor_mes(self.rentabilidade_pedidos_mes_mc_mes,
                                                       self.rentabilidade_pedidos_mes_total_mes,
                                                       self.rentabilidade_pedidos_mes_rentabilidade)
        self.falta_mudar_cor_mes_valor = round(self.falta_mudar_cor_mes[0], 2)
        self.falta_mudar_cor_mes_valor_rentabilidade = round(self.falta_mudar_cor_mes[1], 2)
        self.falta_mudar_cor_mes_porcentagem = round(self.falta_mudar_cor_mes[2], 2)
        self.falta_mudar_cor_mes_cor = self.falta_mudar_cor_mes[3]

        self.data_hora_atual = data_hora_atual()

        self.confere_pedidos = confere_pedidos(self.carteira)

    def get_dados(self):
        dados = {
            'dias_meta': self.dias_meta,
            'carteira': self.carteira,
            'meta_diaria': self.meta_diaria,
            'pedidos_dia': self.pedidos_dia,
            'toneladas_dia': self.toneladas_dia,
            'porcentagem_mc_dia': self.porcentagem_mc_dia,
            'porcentagem_meta_dia': self.porcentagem_meta_dia,
            'faltam_meta_dia': self.faltam_meta_dia,
            'conversao_de_orcamentos': self.conversao_de_orcamentos,
            'faltam_abrir_orcamentos_dia': self.faltam_abrir_orcamentos_dia,
            'meta_mes': self.meta_mes,
            'pedidos_mes': self.pedidos_mes,
            'toneladas_mes': self.toneladas_mes,
            'porcentagem_mc_mes': self.porcentagem_mc_mes,
            'porcentagem_meta_mes': self.porcentagem_meta_mes,
            'faltam_meta_mes': self.faltam_meta_mes,
            'data_hora_atual': self.data_hora_atual,
            'rentabilidade_pedidos_dia': self.rentabilidade_pedidos_dia,
            'cor_rentabilidade_css_dia': self.cor_rentabilidade_pedidos_dia,
            'rentabilidade_pedidos_mes_rentabilidade_mes': self.rentabilidade_pedidos_mes_rentabilidade,
            'cor_rentabilidade_css_mes': self.cor_rentabilidade_pedidos_mes,
            'falta_mudar_cor_mes_valor': self.falta_mudar_cor_mes_valor,
            'falta_mudar_cor_mes_valor_rentabilidade': self.falta_mudar_cor_mes_valor_rentabilidade,
            'falta_mudar_cor_mes_porcentagem': self.falta_mudar_cor_mes_porcentagem,
            'falta_mudar_cor_mes_cor': self.falta_mudar_cor_mes_cor,
            'confere_pedidos': self.confere_pedidos,
        }
        return dados


class DashboardVendasCarteira(DashBoardVendas):
    ...


class DashboardVendasTv(DashBoardVendas):
    def __init__(self) -> None:
        super().__init__()
        self.assistentes_tecnicos = get_assistentes_tecnicos()
        self.agenda_vec = get_assistentes_tecnicos_agenda()

    def get_dados(self):
        dados = super().get_dados()
        dados.update({
            'assistentes_tecnicos': self.assistentes_tecnicos,
            'agenda_vec': self.agenda_vec,
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

        self.frete_cif = frete_cif
        self.carteira_mes = []
        for carteira in get_consultores_tecnicos_ativos():
            rentabilidade_pedidos_mes_ = rentabilidade_pedidos_mes(self.despesa_administrativa_fixa,
                                                                   self.primeiro_dia_mes,
                                                                   self.primeiro_dia_util_mes,
                                                                   self.ultimo_dia_mes,
                                                                   self.primeiro_dia_util_proximo_mes, carteira.nome)
            rentabilidade_pedidos_mes_mc_mes = rentabilidade_pedidos_mes_['mc_mes']
            rentabilidade_pedidos_mes_total_mes = rentabilidade_pedidos_mes_['total_mes']
            rentabilidade_pedidos_mes_rentabilidade = rentabilidade_pedidos_mes_['rentabilidade_mes']
            toneladas_mes = rentabilidade_pedidos_mes_['toneladas_mes']
            cor_rentabilidade_pedidos_mes = cor_rentabilidade_css(rentabilidade_pedidos_mes_rentabilidade)
            meta_mes_float = float(carteira.meta_mes)
            dados_carteira = {
                'carteira': carteira.nome,
                'mc_mes_carteira': rentabilidade_pedidos_mes_mc_mes,
                'meta_mes': meta_mes_float,
                'total_mes_carteira': rentabilidade_pedidos_mes_total_mes,
                'falta_meta': meta_mes_float - rentabilidade_pedidos_mes_total_mes,
                'porcentagem_meta_mes': 0 if meta_mes_float == 0 else int(rentabilidade_pedidos_mes_total_mes / meta_mes_float * 100),
                'rentabilidade_mes_carteira': rentabilidade_pedidos_mes_rentabilidade,
                'toneladas_mes_carteira': toneladas_mes,
                'cor_rentabilidade_mes_carteira': cor_rentabilidade_pedidos_mes,
            }
            self.carteira_mes.append(dados_carteira)

    def get_dados(self):
        dados = super().get_dados()
        dados.update({
            'carteiras_mes': self.carteira_mes,
            'frete_cif': self.frete_cif,
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
    """Confere possiveis erros dos pedidos em aberto"""
    sql = """
        SELECT
            *

        FROM
            (
                SELECT DISTINCT
                    PEDIDOS.NUMPED AS PEDIDO,
                    VENDEDORES.NOMERED AS CONSULTOR,
                    CASE
                        WHEN CLIENTES.ENDERECO LIKE ' %' THEN 'ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO LIKE '% ' THEN 'ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DO CLIENTE EM BRANCO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.FONE1 NOT LIKE '______%' OR CLIENTES.FONE1 LIKE '%I%' OR CLIENTES.FONE1 LIKE '%D%' OR CLIENTES.FONE1 LIKE '%R%' OR CLIENTES.FONE1 LIKE '%*%' THEN 'TELEFONE 1 DO CLIENTE INCORRETO'
                        WHEN PEDIDOS.PEDCLI LIKE ' %' THEN 'PEDIDO DO CLIENTE NO PEDIDO COM ESPACO NO INICIO'
                        WHEN PEDIDOS.PEDCLI LIKE '% ' THEN 'PEDIDO DO CLIENTE NO PEDIDO COM ESPACO NO FIM'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND CLIENTES.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DO CLIENTE DESMARCADO'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND PEDIDOS.BOLETO_NF = 'NAO' THEN 'CAMPO ENVIAR BOLETO JUNTAMENTE COM A NF NO PEDIDO DESMARCADO'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '% %' OR CLIENTES_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '.%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%.' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR CLIENTES_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DO CLIENTE INCORRETO'
                        WHEN NFE_NAC_CLI_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_CLI_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_CLI_EMAILS.EMAIL IS NULL THEN 'EMAIL DE ENVIO DA NFE DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE ' %' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE '% ' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE ' %' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE '% ' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT IS NULL THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE EM BRANCO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.CEP_ENT NOT LIKE '________' THEN 'CEP DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.TIPO IS NULL AND PLATAFORMAS.RAZAO_SOCIAL IS NOT NULL THEN 'TIPO/CNPJ DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND ORDEM_CLIENTE.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DA ORDEM DESMARCADO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE ' %' THEN 'ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE '% ' THEN 'ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DA ORDEM EM BRANCO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND (ORDEM_CLIENTE.FONE1 NOT LIKE '______%' OR ORDEM_CLIENTE.FONE1 LIKE '%I%' OR ORDEM_CLIENTE.FONE1 LIKE '%D%' OR ORDEM_CLIENTE.FONE1 LIKE '%R%' OR ORDEM_CLIENTE.FONE1 LIKE '%*%') THEN 'TELEFONE 1 DA ORDEM INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (ORDEM_EMAILS_BOLETOS.EMAIL LIKE '% %' OR ORDEM_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '.%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%.' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR ORDEM_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DA ORDEM INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND (NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_ORDEM_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_ORDEM_EMAILS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DA NFE DA ORDEM INCORRETO'
                        WHEN TRANSPORTADORAS.EMAIL_NFE LIKE '% %' OR TRANSPORTADORAS.EMAIL_NFE NOT LIKE '%_@_%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%,%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%>%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%<%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '.%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%.' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%..%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%""%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%(%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%)%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%;%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%\\%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%[%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%]%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%!%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%#%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%$%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%*%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%/%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%?%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%|%' THEN 'EMAIL DE ENVIO DA NFE DA TRANSPORTADORA INCORRETO'
                        WHEN PEDIDOS.TEXTO1 LIKE '%–%' OR PEDIDOS.TEXTO2 LIKE '%–%' OR PEDIDOS.TEXTO3 LIKE '%–%' OR PEDIDOS.TEXTO4 LIKE '%–%' OR PEDIDOS.TEXTO5 LIKE '%–%' OR PEDIDOS.TEXTO6 LIKE '%–%' THEN 'CARACTERES INVALIDOS NOS TEXTOS LEGAIS'
                        WHEN PEDIDOS.DESTINO != PEDIDOS_ITENS.DESTINO_MERCADORIAS THEN 'DESTINO DAS MERCADORIAS DA CAPA DO ORMANENTO E A DOS ITENS ESTAO DIFERENTES'
                        WHEN CLIENTES.ISENTO_INSCRICAO = 'SIM' AND CLIENTES.INDICADOR_IE != 9 OR CLIENTES.ISENTO_INSCRICAO = 'NAO' AND CLIENTES.INDICADOR_IE != 1 THEN 'INDICADOR DA INSCRICAO ESTADUAL DO CLIENTE INCORRETA'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND CLIENTES.ISENTO_INSCRICAO != 'NAO' OR PEDIDOS.CHAVE_TIPO = 51 AND CLIENTES.ISENTO_INSCRICAO != 'SIM' THEN 'TIPO DE PEDIDO INCORRETO'
                        WHEN (PEDIDOS.COBRANCA_FRETE = 0 AND PEDIDOS.VALOR_FRETE != 0) OR (PEDIDOS.COBRANCA_FRETE = 1 AND PEDIDOS.VALOR_FRETE = 0) OR (PEDIDOS.COBRANCA_FRETE = 2 AND (PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR PEDIDOS.COBRANCA_FRETE = 3 OR (PEDIDOS.COBRANCA_FRETE = 4 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR (PEDIDOS.COBRANCA_FRETE = 5 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR PEDIDOS.VALOR_FRETE = 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR (PEDIDOS.COBRANCA_FRETE = 6 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (7738, 8012) OR PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR PEDIDOS.COBRANCA_FRETE = 9 THEN 'CONTRATACAO DE FRETE INCORRETO'
                        WHEN CLIENTES.EMAIL_NFE_SEM_ANEXOS = 'SIM' THEN 'CLIENTE MARCADO PARA NAO INCLUIR ANEXOS NO EMAIL DA NFE'
                        WHEN CONTATOS.FONEC IS NULL AND CONTATOS.CELULAR IS NULL THEN 'CONTATO DE ENTREGA DO PEDIDO SEM NUMERO'
                        WHEN PEDIDOS.CHAVE_TIPO IN (47, 71, 12, 36) AND (PRODUTOS.CHAVE_FAMILIA != 8378 AND PRODUTOS.PESO_LIQUIDO != PRODUTOS.CUBAGEM OR PRODUTOS.CHAVE_FAMILIA = 8378 AND PRODUTOS.CUBAGEM = 0) THEN 'INFORMAR TI, PESO ESPECIFICO INCORRETO'
                        WHEN PEDIDOS.PEDCLI IS NULL OR PEDIDOS.PEDCLI NOT LIKE '%____%' OR (PEDIDOS.PEDCLI IS NULL AND PEDIDOS_ITENS.PEDCLI IS NOT NULL AND PEDIDOS_ITENS.PEDCLI NOT LIKE '%____%') THEN 'PEDIDO DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.UF_ENT != CLIENTES.UF AND PLATAFORMAS.CNPJ_CPF = CLIENTES.CGC AND PLATAFORMAS.INSCRICAO = CLIENTES.INSCRICAO THEN 'INSCRICAO ESTADUAL DO ENDERECO DE ENTREGA INCORRETA'
                        WHEN TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5) AND (PEDIDOS.VALOR_FRETE_EMPRESA IS NULL OR PEDIDOS.VALOR_FRETE_EMPRESA = 0) THEN 'PREENCHER VALOR FRETE COPLAS/EMPRESA'
                        WHEN CLIENTES.CHAVE_TIPO IN (7908, 7904, 7911) AND PRODUTOS.CODIGO LIKE '%TAMPAO%' AND PRODUTOS.CODIGO NOT LIKE '%CLARO%' THEN 'TROCAR PARA TAMPAO CLARO'
                    END AS ERRO

                FROM
                    COPLAS.CONTATOS,
                    COPLAS.PEDIDOS_ITENS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.NFE_NAC_CLI_EMAILS) NFE_NAC_ORDEM_EMAILS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.CLIENTES_EMAILS_BOLETOS) ORDEM_EMAILS_BOLETOS,
                    (SELECT CODCLI, ENDERECO, ENDERECO_NUMERO, ENDERECO_COMPLEMENTO, FONE1, ENVIAR_BOLETO_PDF FROM COPLAS.CLIENTES) ORDEM_CLIENTE,
                    COPLAS.PLATAFORMAS,
                    COPLAS.NFE_NAC_CLI_EMAILS,
                    COPLAS.CLIENTES_EMAILS_BOLETOS,
                    COPLAS.VENDEDORES,
                    COPLAS.TRANSPORTADORAS,
                    COPLAS.PEDIDOS,
                    COPLAS.CLIENTES,
                    COPLAS.PRODUTOS

                WHERE
                    PEDIDOS.CHAVE_CONTATO_ENTREGA = CONTATOS.CHAVE(+) AND
                    PEDIDOS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
                    NFE_NAC_ORDEM_EMAILS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_EMAILS_BOLETOS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_CLIENTE.CODCLI(+) = PEDIDOS.CHAVE_CLIENTE_REMESSA AND
                    PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
                    CLIENTES.CODCLI = NFE_NAC_CLI_EMAILS.CHAVE_CLIENTE(+) AND
                    CLIENTES.CODCLI = CLIENTES_EMAILS_BOLETOS.CHAVE_CLIENTE(+) AND
                    VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                    PEDIDOS.CHAVE_TRANSPORTADORA = TRANSPORTADORAS.CODTRANSP AND
                    PEDIDOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND

                    -- place holder para selecionar carteira
                    VENDEDORES.NOMERED LIKE :carteira AND

                    PEDIDOS.STATUS != 'LIQUIDADO'
                    -- PEDIDOS.DATA_PEDIDO >= TO_DATE('01/10/2024', 'DD-MM-YYYY')
            )

        WHERE
            ERRO IS NOT NULL
    """

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


def map_relatorio_vendas_sql_string_placeholders(fonte: Literal['orcamentos', 'pedidos', 'faturamentos'], trocar_para_itens_excluidos: bool = False, **kwargs_formulario):
    """
        SQLs estão em um dict onde a chave é o nome do campo do formulario e o valor é um dict com o placeholder como
        chave e o codigo sql como valor
    """
    incluir_orcamentos_oportunidade = kwargs_formulario.pop('incluir_orcamentos_oportunidade', False)
    incluir_orcamentos_oportunidade = "" if incluir_orcamentos_oportunidade else "ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND"

    notas_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    notas_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE), 0), 2) AS MC_VALOR"
    notas_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR
    """

    notas_lfrete_from = """
        (
            SELECT
                CHAVE_NOTA_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

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

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM NOTAS.DATA_EMISSAO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM NOTAS.DATA_EMISSAO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

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
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': notas_lfrete_cor_coluna,
                                     'lfrete_from': notas_lfrete_from,
                                     'lfrete_join': notas_lfrete_join, },

        'coluna_documento': {'documento_campo_alias': "NOTAS.NF AS DOCUMENTO,",
                             'documento_campo': "NOTAS.NF,", },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "",
                                      'data_entrega_itens_campo': "", },

        'coluna_status_documento': {'status_documento_campo_alias': "",
                                    'status_documento_campo': "", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "",
                                          'orcamento_oportunidade_campo': "", },
    }

    pedidos_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    pedidos_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END), 0), 2) AS MC_VALOR"
    pedidos_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR
    """
    pedidos_lfrete_from = """
        (
            SELECT
                CHAVE_PEDIDO_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

            FROM
                (
                    {lfrete_pedidos} AND

                        PEDIDOS.DATA_PEDIDO >= :data_inicio AND
                        PEDIDOS.DATA_PEDIDO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_PEDIDO_ITEM
        ) LFRETE,
    """.format(lfrete_pedidos=lfrete_pedidos)
    pedidos_lfrete_join = "LFRETE.CHAVE_PEDIDO_ITEM = PEDIDOS_ITENS.CHAVE AND"

    map_sql_pedidos_base = {
        'valor_mercadorias': "SUM((PEDIDOS_ITENS.VALOR_TOTAL - (COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0), 0))) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': "",

        'fonte_itens': "COPLAS.PEDIDOS_ITENS,",

        'fonte': "COPLAS.PEDIDOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
            PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
        """,

        'fonte_where': "PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND",

        'fonte_where_data': """
            PEDIDOS.DATA_PEDIDO >= :data_inicio AND
            PEDIDOS.DATA_PEDIDO <= :data_fim
        """,
    }

    map_sql_pedidos = {
        'coluna_media_dia': {'media_dia_campo_alias': "SUM((PEDIDOS_ITENS.VALOR_TOTAL - (COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0), 0))) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END) / COUNT(DISTINCT PEDIDOS.DATA_PEDIDO) AS MEDIA_DIA,"},

        'coluna_data_emissao': {'data_emissao_campo_alias': "PEDIDOS.DATA_PEDIDO AS DATA_EMISSAO,",
                                'data_emissao_campo': "PEDIDOS.DATA_PEDIDO,", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM PEDIDOS.DATA_PEDIDO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM PEDIDOS.DATA_PEDIDO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM PEDIDOS.DATA_PEDIDO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

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

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(PEDIDOS_ITENS.PRECO_TABELA) AS PRECO_TABELA_INCLUSAO,",
                                         'preco_tabela_inclusao_campo': "MAX(PEDIDOS_ITENS.PRECO_TABELA),", },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(PEDIDOS_ITENS.PRECO_VENDA), 2) AS PRECO_VENDA_MEDIO,",
                                     'preco_venda_medio_campo': "ROUND(AVG(PEDIDOS_ITENS.PRECO_VENDA), 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(PEDIDOS_ITENS.QUANTIDADE) AS QUANTIDADE,",
                              'quantidade_campo': "SUM(PEDIDOS_ITENS.QUANTIDADE),", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': "", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "", },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT PEDIDOS.NUMPED) AS QUANTIDADE_DOCUMENTOS,",
                                         'quantidade_documentos_campo': "COUNT(DISTINCT PEDIDOS.NUMPED),", },

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

        'coluna_rentabilidade': {'lfrete_coluna': pedidos_lfrete_coluna,
                                 'lfrete_valor_coluna': pedidos_lfrete_valor_coluna,
                                 'lfrete_from': pedidos_lfrete_from,
                                 'lfrete_join': pedidos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': pedidos_lfrete_coluna,
                                       'lfrete_valor_coluna': pedidos_lfrete_valor_coluna,
                                       'lfrete_from': pedidos_lfrete_from,
                                       'lfrete_join': pedidos_lfrete_join, },
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': pedidos_lfrete_cor_coluna,
                                     'lfrete_from': pedidos_lfrete_from,
                                     'lfrete_join': pedidos_lfrete_join, },

        'coluna_documento': {'documento_campo_alias': "PEDIDOS.NUMPED AS DOCUMENTO,",
                             'documento_campo': "PEDIDOS.NUMPED,", },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "PEDIDOS_ITENS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "PEDIDOS_ITENS.DATA_ENTREGA,", },

        'coluna_status_documento': {'status_documento_campo_alias': "PEDIDOS.STATUS AS STATUS_DOCUMENTO,",
                                    'status_documento_campo': "PEDIDOS.STATUS,", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "PEDIDOS.STATUS IN ('EM ABERTO', 'BLOQUEADO') AND", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "",
                                          'orcamento_oportunidade_campo': "", },
    }

    orcamentos_status_produto_orcamento_tipo_from = "COPLAS.STATUS_ORCAMENTOS_ITENS,"
    orcamentos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS.STATUS AND"

    orcamentos_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    orcamentos_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END), 0), 2) AS MC_VALOR"
    orcamentos_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7767 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR
    """
    orcamentos_lfrete_from = """
        (
            SELECT
                CHAVE_ORCAMENTO_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7767 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL ELSE 0 END), 2) AS MC_SEM_FRETE_PQ

            FROM
                (
                    {lfrete_orcamentos} AND

                        {incluir_orcamentos_oportunidade}
                        ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
                        ORCAMENTOS.DATA_PEDIDO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_ORCAMENTO_ITEM
        ) LFRETE,
    """.format(lfrete_orcamentos=lfrete_orcamentos, incluir_orcamentos_oportunidade=incluir_orcamentos_oportunidade)
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
            {incluir_orcamentos_oportunidade}
            ORCAMENTOS.NUMPED != 204565 AND
        """.format(incluir_orcamentos_oportunidade=incluir_orcamentos_oportunidade),

        'fonte_where_data': """
            ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
            ORCAMENTOS.DATA_PEDIDO <= :data_fim
        """,
    }

    map_sql_orcamentos = {
        'coluna_media_dia': {'media_dia_campo_alias': "SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0), 0))) * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END) / COUNT(DISTINCT ORCAMENTOS.DATA_PEDIDO) AS MEDIA_DIA,"},

        'coluna_data_emissao': {'data_emissao_campo_alias': "ORCAMENTOS.DATA_PEDIDO AS DATA_EMISSAO,",
                                'data_emissao_campo': "ORCAMENTOS.DATA_PEDIDO,", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM ORCAMENTOS.DATA_PEDIDO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

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
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': orcamentos_lfrete_cor_coluna,
                                     'lfrete_from': orcamentos_lfrete_from,
                                     'lfrete_join': orcamentos_lfrete_join, },

        'coluna_documento': {'documento_campo_alias': "ORCAMENTOS.NUMPED AS DOCUMENTO,",
                             'documento_campo': "ORCAMENTOS.NUMPED,", },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "ORCAMENTOS_ITENS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "ORCAMENTOS_ITENS.DATA_ENTREGA,", },

        'coluna_status_documento': {'status_documento_campo_alias': "ORCAMENTOS.STATUS AS STATUS_DOCUMENTO,",
                                    'status_documento_campo': "ORCAMENTOS.STATUS,", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "ORCAMENTOS.STATUS IN ('EM ABERTO', 'BLOQUEADO') AND", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "ORCAMENTOS.REGISTRO_OPORTUNIDADE AS OPORTUNIDADE,",
                                          'orcamento_oportunidade_campo': "ORCAMENTOS.REGISTRO_OPORTUNIDADE,", },
    }

    # Itens de orçamento excluidos somente o que difere de orçamento

    orcamentos_itens_excluidos_status_produto_orcamento_tipo_from = orcamentos_status_produto_orcamento_tipo_from
    orcamentos_itens_excluidos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS_EXCLUIDOS.STATUS AND"

    orcamentos_itens_excluidos_lfrete_coluna = ", 0 AS MC"
    orcamentos_itens_excluidos_lfrete_valor_coluna = ", 0 AS MC_VALOR"
    orcamentos_itens_excluidos_lfrete_cor_coluna = ", 0 AS MC_COR"
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
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': orcamentos_itens_excluidos_lfrete_cor_coluna,
                                     'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                     'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "ORCAMENTOS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "ORCAMENTOS.DATA_ENTREGA,", },
    }

    sql_final = {}
    if fonte == 'orcamentos':
        sql_final.update(map_sql_orcamentos_base)
        if trocar_para_itens_excluidos:
            sql_final.update(map_sql_orcamentos_base_itens_excluidos)
    elif fonte == 'pedidos':
        sql_final.update(map_sql_pedidos_base)
    else:
        sql_final.update(map_sql_notas_base)

    for chave, valor in kwargs_formulario.items():
        if valor:
            if fonte == 'orcamentos':
                get_map_orcamento = map_sql_orcamentos.get(chave)
                if get_map_orcamento:
                    sql_final.update(get_map_orcamento)  # type:ignore
                    if trocar_para_itens_excluidos:
                        get_map_orcamento_itens_excluidos = map_sql_orcamentos_itens_excluidos.get(chave)
                        if get_map_orcamento_itens_excluidos:
                            sql_final.update(get_map_orcamento_itens_excluidos)  # type:ignore
            elif fonte == 'pedidos':
                get_map_pedido = map_sql_pedidos.get(chave)
                if get_map_pedido:
                    sql_final.update(get_map_pedido)  # type:ignore
            else:
                get_map_nota = map_sql_notas.get(chave)
                if get_map_nota:
                    sql_final.update(get_map_nota)  # type:ignore

    return sql_final


def get_relatorios_vendas(fonte: Literal['orcamentos', 'pedidos', 'faturamentos'], **kwargs):
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

    kwargs_sql.update(map_relatorio_vendas_sql_string_placeholders(fonte, **kwargs))
    if trocar_para_itens_excluidos:
        kwargs_sql_itens_excluidos.update(map_relatorio_vendas_sql_string_placeholders(
            fonte, trocar_para_itens_excluidos, **kwargs))  # type:ignore

    # kwargs_ora precisa conter os placeholders corretamente

    if grupo_economico:
        kwargs_ora.update({'grupo_economico': grupo_economico, })

    if carteira:
        chave_carteira = carteira.chave_analysis
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
        chave_estado = estado.chave_analysis
        kwargs_ora.update({'chave_estado': chave_estado, })

    if status_produto_orcamento:
        if fonte == 'orcamentos':
            chave_status_produto_orcamento = status_produto_orcamento.DESCRICAO
            kwargs_ora.update({'chave_status_produto_orcamento': chave_status_produto_orcamento, })

    if status_produto_orcamento_tipo:
        if fonte == 'orcamentos':
            if status_produto_orcamento_tipo != "PERDIDO_CANCELADO":
                kwargs_ora.update({'status_produto_orcamento_tipo': status_produto_orcamento_tipo, })

    sql_base = """
        SELECT
            {data_emissao_campo_alias}
            {data_entrega_itens_campo_alias}
            {ano_mes_emissao_campo_alias}
            {ano_emissao_campo_alias}
            {mes_emissao_campo_alias}
            {dia_emissao_campo_alias}
            {documento_campo_alias}
            {orcamento_oportunidade_campo_alias}
            {status_documento_campo_alias}
            {carteira_campo_alias}
            {grupo_economico_campo_alias}
            {cliente_campo_alias}
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
            {lfrete_coluna_cor}

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
            {status_documento_em_aberto_pesquisa}
            {carteira_parede_de_concreto_pesquisa}
            {carteira_premoldado_poste_pesquisa}

            {fonte_where_data}

        GROUP BY
            {data_emissao_campo}
            {data_entrega_itens_campo}
            {ano_mes_emissao_campo}
            {ano_emissao_campo}
            {mes_emissao_campo}
            {dia_emissao_campo}
            {documento_campo}
            {orcamento_oportunidade_campo}
            {status_documento_campo}
            {carteira_campo}
            {grupo_economico_campo}
            {cliente_campo}
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
            {dia_emissao_campo}
            {documento_campo}
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

        alias_para_header_groupby = ['DATA_EMISSAO', 'ANO_EMISSAO', 'MES_EMISSAO', 'DIA_EMISSAO', 'ANO_MES_EMISSAO',
                                     'CHAVE_GRUPO_ECONOMICO', 'GRUPO', 'CARTEIRA', 'TIPO_CLIENTE', 'FAMILIA_PRODUTO',
                                     'PRODUTO', 'UNIDADE', 'CIDADE_PRINCIPAL', 'UF_PRINCIPAL', 'STATUS', 'STATUS_TIPO',
                                     'DOCUMENTO', 'CLIENTE', 'DATA_ENTREGA', 'STATUS_DOCUMENTO', 'OPORTUNIDADE',]
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
            dt_resultado_final = dt_resultado_final.sort_values(by='VALOR_MERCADORIAS', ascending=False)
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
