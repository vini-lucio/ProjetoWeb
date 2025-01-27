from utils.oracle.conectar import executar_oracle
from utils.lfrete import pedidos as lfrete_pedidos
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import (get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda,
                              get_transportadoras)
from frete.services import get_dados_pedidos_em_aberto, get_transportadoras_valores_atendimento
from django.core.exceptions import ObjectDoesNotExist


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

        self.PEDIDOS_DIA, self.TONELADAS_DIA = pedidos_dia(self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.PORCENTAGEM_META_DIA = int(self.PEDIDOS_DIA / self.META_DIARIA * 100)
        self.FALTAM_META_DIA = round(self.META_DIARIA - self.PEDIDOS_DIA, 2)
        self.CONVERSAO_DE_ORCAMENTOS = conversao_de_orcamentos()
        self.FALTAM_ABRIR_ORCAMENTOS_DIA = round(self.FALTAM_META_DIA / (self.CONVERSAO_DE_ORCAMENTOS / 100), 2)
        self.PEDIDOS_MES, self.TONELADAS_MES = pedidos_mes(self.PRIMEIRO_DIA_MES, self.PRIMEIRO_DIA_UTIL_MES,
                                                           self.ULTIMO_DIA_MES, self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.PORCENTAGEM_META_MES = int(self.PEDIDOS_MES / self.META_MES * 100)
        self.FALTAM_META_MES = round(self.META_MES - self.PEDIDOS_MES, 2)

        self.RENTABILIDADE_PEDIDOS_DIA = rentabilidade_pedidos_dia(self.DESPESA_ADMINISTRATIVA_FIXA,
                                                                   self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.COR_RENTABILIDADE_PEDIDOS_DIA = cor_rentabilidade_css(self.RENTABILIDADE_PEDIDOS_DIA)

        self.RENTABILIDADE_PEDIDOS_MES = rentabilidade_pedidos_mes(self.DESPESA_ADMINISTRATIVA_FIXA,
                                                                   self.PRIMEIRO_DIA_MES,
                                                                   self.PRIMEIRO_DIA_UTIL_MES,
                                                                   self.ULTIMO_DIA_MES,
                                                                   self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.RENTABILIDADE_PEDIDOS_MES_MC_MES = self.RENTABILIDADE_PEDIDOS_MES['mc_mes']
        self.RENTABILIDADE_PEDIDOS_MES_TOTAL_MES_SEM_CONVERTER_MOEDA = (
            self.RENTABILIDADE_PEDIDOS_MES['total_mes_sem_converter_moeda'])
        self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE = self.RENTABILIDADE_PEDIDOS_MES['rentabilidade_mes']
        self.COR_RENTABILIDADE_PEDIDOS_MES = cor_rentabilidade_css(self.RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE)

        self.FALTA_MUDAR_COR_MES = falta_mudar_cor_mes(self.RENTABILIDADE_PEDIDOS_MES_MC_MES,
                                                       self.RENTABILIDADE_PEDIDOS_MES_TOTAL_MES_SEM_CONVERTER_MOEDA,
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


def pedidos_dia(primeiro_dia_util_proximo_mes: str) -> tuple[float, float]:
    """Valor mercadorias e toneladas dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
    sql = """
        SELECT
            ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END), 2) AS TOTAL,
            ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.PESO_LIQUIDO ELSE 0 END) / 1000, 3) AS TONELADAS_PROPRIO

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
            PEDIDOS_ITENS.DATA_ENTREGA <= TO_DATE(:primeiro_dia_util_proximo_mes,'DD-MM-YYYY')
    """

    resultado = executar_oracle(sql, primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    if not resultado[0][0]:
        return 0.00, 0.00

    return float(resultado[0][0]), float(resultado[0][1])


def rentabilidade_pedidos_dia(despesa_administrativa_fixa: float, primeiro_dia_util_proximo_mes: str) -> float:
    """Rentabilidade dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
    sql = """
        SELECT
            -- despesa administrativa (ultima subtração)
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - :despesa_administrativa_fixa AS RENTABILIDADE

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
                                {lfrete} AND

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

    sql = sql.format(lfrete=lfrete_pedidos)

    resultado = executar_oracle(sql, despesa_administrativa_fixa=despesa_administrativa_fixa,
                                primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    # não consegui identificar o porque, não esta retornado [(none,),] e sim [], indice [0][0] não funciona
    if not resultado:
        return 0.00

    return float(resultado[0][0])


def conversao_de_orcamentos():
    """Taxa de conversão de orçamentos com valor comercial dos ultimos 90 dias, ignorando orçamentos oportunidade e palavras chave de erros internos"""
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
                    COPLAS.ORCAMENTOS_ITENS

                WHERE
                    ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
                    ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                    ORCAMENTOS.DATA_PEDIDO >= SYSDATE - 90 AND

                    (
                        ORCAMENTOS_ITENS.STATUS NOT IN ('CANCELADO', 'PERDA P/ OUTROS') OR
                        (
                            ORCAMENTOS_ITENS.STATUS IN ('CANCELADO', 'PERDA P/ OUTROS') AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA LIKE '____%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%ABRIU OUTRO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%ALTE_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%AMOSTRA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%DUAS V%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%DUPLI%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE 'ERRAD_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '% ERRAD_' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '% ERRAD_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE 'ERRO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '% ERRO' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '% ERRO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRA%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCA%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDEI%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%CNPJ%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%MATERIAL%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%CPF%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%PRODUTO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%ITE_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%MUDOU%MODELO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%CNPJ%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%MATERIAL%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%CPF%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%PRODUTO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%ITE_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%MODELO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%OR_AMENTO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%PEDIDO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%OUTRO%CADASTRO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%REPLI%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%SEPARA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%SUBS%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TESTE%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCA%ITE_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCA%MATERIA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCA%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%CNPJ%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%MATERIAL%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%CPF%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%PRODUTO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%MEDIDA%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%ITE_%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROCO%MODELO%' AND
                            ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA NOT LIKE '%TROQU%'
                        )
                    )

                UNION ALL

                SELECT
                    0 AS FECHADO,
                    ROUND(SUM(ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA * ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE), 2) AS TOTAL

                FROM
                    COPLAS.ORCAMENTOS,
                    COPLAS.ORCAMENTOS_ITENS_EXCLUIDOS

                WHERE
                    ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_ORCAMENTO AND
                    ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                    ORCAMENTOS.DATA_PEDIDO >= SYSDATE - 90 AND
                    (
                        ORCAMENTOS_ITENS_EXCLUIDOS.STATUS NOT IN ('CANCELADO', 'PERDA P/ OUTROS') OR
                        (
                            ORCAMENTOS_ITENS_EXCLUIDOS.STATUS IN ('CANCELADO', 'PERDA P/ OUTROS') AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA LIKE '____%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%ABRIU OUTRO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%ALTE_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%AMOSTRA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%DUAS V%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%DUPLI%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE 'ERRAD_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '% ERRAD_' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '% ERRAD_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE 'ERRO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '% ERRO' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '% ERRO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRA%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCA%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDEI%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%CNPJ%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%MATERIAL%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%CPF%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%PRODUTO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%ITE_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%MUDOU%MODELO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%CNPJ%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%MATERIAL%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%CPF%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%PRODUTO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%ITE_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%MODELO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%OR_AMENTO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%PEDIDO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%OUTRO%CADASTRO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%REPLI%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%SEPARA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%SUBS%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TESTE%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCA%ITE_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCA%MATERIA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCA%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%CNPJ%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%QUANTIDADE%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%MATERIAL%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%CPF%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%PRODUTO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%MEDIDA%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%ITE_%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROCO%MODELO%' AND
                            ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA NOT LIKE '%TROQU%'
                        )
                    )
            ) CONVERSAO
    """

    resultado = executar_oracle(sql)

    if not resultado[0][0]:
        return 0.00

    return float(resultado[0][0])


def pedidos_mes(primeiro_dia_mes: str, primeiro_dia_util_mes: str,
                ultimo_dia_mes: str, primeiro_dia_util_proximo_mes: str) -> tuple[float, float]:
    """Valor mercadorias e toneladas dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes, debitando as notas de devolução"""
    sql = """
        SELECT
            ROUND(SUM((PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)) * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT MAX(VALOR) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END) + DEVOLUCOES.TOTAL, 2) AS TOTAL,
            ROUND(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.PESO_LIQUIDO ELSE 0 END) / 1000, 3) AS TONELADAS_PROPRIO

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
                    NOTAS.DATA_EMISSAO >= TO_DATE(:primeiro_dia_mes,'DD-MM-YYYY') AND
                    -- ultimo dia do mes
                    NOTAS.DATA_EMISSAO <= TO_DATE(:ultimo_dia_mes,'DD-MM-YYYY')
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
            DEVOLUCOES.TOTAL
    """

    resultado = executar_oracle(sql, primeiro_dia_mes=primeiro_dia_mes, primeiro_dia_util_mes=primeiro_dia_util_mes,
                                ultimo_dia_mes=ultimo_dia_mes, primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    if not resultado[0][0]:
        return 0.00, 0.00

    return float(resultado[0][0]), float(resultado[0][1])


def rentabilidade_pedidos_mes(despesa_administrativa_fixa: float, primeiro_dia_mes: str,
                              primeiro_dia_util_mes: str, ultimo_dia_mes: str,
                              primeiro_dia_util_proximo_mes: str) -> dict[str, float]:
    """Rentabilidade dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes"""
    sql = """
        SELECT
            ROUND((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100), 2) AS MC_MES,
            TOTAL_MES,

            -- despesa administrativa (ultima subtração)
            ROUND(((TOTAL_MES_PP * ((-1) + RENTABILIDADE_PP) / 100) + (TOTAL_MES_PT * (4 + RENTABILIDADE_PT) / 100) + (TOTAL_MES_PQ * (4 + RENTABILIDADE_PQ) / 100)) / TOTAL_MES * 100, 2) - :despesa_administrativa_fixa AS RENTABILIDADE

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

    sql = sql.format(lfrete=lfrete_pedidos)

    resultado = executar_oracle(sql, despesa_administrativa_fixa=despesa_administrativa_fixa,
                                primeiro_dia_mes=primeiro_dia_mes, primeiro_dia_util_mes=primeiro_dia_util_mes,
                                ultimo_dia_mes=ultimo_dia_mes, primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes)

    mc_mes = 0.0 if not resultado[0][0] else resultado[0][0]
    total_mes_sem_converter_moeda = 0.0 if not resultado[0][1] else resultado[0][1]
    rentabilidade_mes = 0.0 if not resultado[0][2] else resultado[0][2]

    dicionario = {
        'mc_mes': float(mc_mes),
        'total_mes_sem_converter_moeda': float(total_mes_sem_converter_moeda),
        'rentabilidade_mes': float(rentabilidade_mes)
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
                                                    transportadora_especifica=True)
        except ObjectDoesNotExist:
            transportadora = transportadoras.filter(chave_analysis=dados_pedido['CHAVE_TRANSPORTADORA'])
            if transportadora:
                pedido = dados_pedido['PEDIDO']
                consultor = dados_pedido['CARTEIRA']
                erro = 'TRANSPORTADORA NÃO ATENDE O DESTINO'
                erros.append({'PEDIDO': pedido, 'CONSULTOR': consultor, 'ERRO': erro})

    return erros
