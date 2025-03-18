from utils.oracle.conectar import executar_oracle
from utils.lfrete import pedidos as lfrete_pedidos
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import (get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda,
                              get_transportadoras, get_consultores_tecnicos_ativos)
from utils.lfrete import notas as lfrete_notas
from frete.services import get_dados_pedidos_em_aberto, get_transportadoras_valores_atendimento
from home.services import frete_cif_ano_mes_a_mes, faturado_bruto_ano_mes_a_mes
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


def rentabilidade_pedidos_dia(despesa_administrativa_fixa: float, primeiro_dia_util_proximo_mes: str,
                              carteira: str = '%%') -> tuple[float, float, float]:
    """Valor mercadorias, toneladas de produto proprio e rentabilidade dos pedidos com valor comercial no dia com entrega até o primeiro dia util do proximo mes"""
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
                                primeiro_dia_util_proximo_mes=primeiro_dia_util_proximo_mes, carteira=carteira)

    # não consegui identificar o porque, não esta retornado [(none,),] e sim [], indice [0][0] não funciona
    if not resultado:
        return 0.00, 0.00, 0.00,

    return float(resultado[0][0]), float(resultado[0][1]), float(resultado[0][2]),


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


def rentabilidade_pedidos_mes(despesa_administrativa_fixa: float, primeiro_dia_mes: str,
                              primeiro_dia_util_mes: str, ultimo_dia_mes: str,
                              primeiro_dia_util_proximo_mes: str, carteira: str = '%%') -> dict[str, float]:
    """Valor mercadorias, toneladas de produto proprio e rentabilidade dos pedidos com valor comercial no mes com entrega até o primeiro dia util do proximo mes"""
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


def get_relatorios_supervisao(data_inicio, data_fim, coluna_grupo_economico: bool, grupo_economico,
                              coluna_carteira: bool, chave_carteira, coluna_tipo_cliente: bool, chave_tipo_cliente,
                              coluna_produto: bool, produto, coluna_rentabilidade: bool):
    kwargs_sql = {}
    kwargs_ora = {}

    # Grupo Economico coluna e filtro

    grupo_economico_campo_alias = ""
    grupo_economico_campo = ""
    if coluna_grupo_economico:
        grupo_economico_campo_alias = "GRUPO_ECONOMICO.DESCRICAO AS GRUPO,"
        grupo_economico_campo = "GRUPO_ECONOMICO.DESCRICAO,"
    kwargs_sql.update({'grupo_economico_campo_alias': grupo_economico_campo_alias,
                       'grupo_economico_campo': grupo_economico_campo})

    grupo_economico_pesquisa = ""
    if grupo_economico:
        grupo_economico_pesquisa = "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND"
        kwargs_ora.update({'grupo_economico': grupo_economico, })
    kwargs_sql.update({'grupo_economico_pesquisa': grupo_economico_pesquisa, })

    # Carteira coluna e filtro

    carteira_campo_alias = ""
    carteira_campo = ""
    if coluna_carteira:
        carteira_campo_alias = "VENDEDORES.NOMERED AS CARTEIRA,"
        carteira_campo = "VENDEDORES.NOMERED,"
    kwargs_sql.update({'carteira_campo_alias': carteira_campo_alias,
                       'carteira_campo': carteira_campo})

    carteira_pesquisa = ""
    if chave_carteira:
        carteira_pesquisa = "VENDEDORES.CODVENDEDOR = :chave_carteira AND"
        kwargs_ora.update({'chave_carteira': chave_carteira, })
    kwargs_sql.update({'carteira_pesquisa': carteira_pesquisa, })

    # Tipo de Cliente coluna e filtro

    tipo_cliente_campo_alias = ""
    tipo_cliente_campo = ""
    if coluna_tipo_cliente:
        tipo_cliente_campo_alias = "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,"
        tipo_cliente_campo = "CLIENTES_TIPOS.DESCRICAO,"
    kwargs_sql.update({'tipo_cliente_campo_alias': tipo_cliente_campo_alias,
                       'tipo_cliente_campo': tipo_cliente_campo})

    tipo_cliente_pesquisa = ""
    if chave_tipo_cliente:
        tipo_cliente_pesquisa = "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND"
        kwargs_ora.update({'chave_tipo_cliente': chave_tipo_cliente, })
    kwargs_sql.update({'tipo_cliente_pesquisa': tipo_cliente_pesquisa, })

    # Produto coluna e filtro

    produto_campo_alias = ""
    produto_campo = ""
    if coluna_produto:
        produto_campo_alias = "PRODUTOS.CODIGO AS PRODUTO,"
        produto_campo = "PRODUTOS.CODIGO,"
    kwargs_sql.update({'produto_campo_alias': produto_campo_alias,
                       'produto_campo': produto_campo})

    produto_pesquisa = ""
    if produto:
        produto_pesquisa = "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND"
        kwargs_ora.update({'produto': produto, })
    kwargs_sql.update({'produto_pesquisa': produto_pesquisa, })

    # Rentabilidade coluna

    lfrete_coluna = ""
    lfrete_from = ""
    lfrete_join = ""
    if coluna_rentabilidade:
        lfrete_coluna = ", ROUND(SUM(LFRETE.MC_SEM_FRETE) / SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)) * 100, 2) AS RENTABILIDADE"
        lfrete_from = """
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
        """
        lfrete_from = lfrete_from.format(lfrete_notas=lfrete_notas)
        lfrete_join = "LFRETE.CHAVE_NOTA_ITEM = NOTAS_ITENS.CHAVE AND"
    kwargs_sql.update({'lfrete_coluna': lfrete_coluna, 'lfrete_from': lfrete_from, 'lfrete_join': lfrete_join, })

    sql = """
        SELECT
            {carteira_campo_alias}
            {grupo_economico_campo_alias}
            {tipo_cliente_campo_alias}
            {produto_campo_alias}
            SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)) AS VALOR_MERCADORIAS
            {lfrete_coluna}

        FROM
            {lfrete_from}
            (
                SELECT
                    NOTAS_ITENS.CHAVE_NOTA,
                    SUM(NOTAS_ITENS.PESO_LIQUIDO) AS PESO_LIQUIDO

                FROM
                    COPLAS.NOTAS_ITENS

                GROUP BY
                    NOTAS_ITENS.CHAVE_NOTA
            ) NOTAS_PESO_LIQUIDO,
            COPLAS.VENDEDORES,
            COPLAS.NOTAS_ITENS,
            COPLAS.NOTAS,
            COPLAS.PRODUTOS,
            COPLAS.GRUPO_ECONOMICO,
            COPLAS.CLIENTES,
            COPLAS.CLIENTES_TIPOS

        WHERE
            {lfrete_join}
            PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CHAVE_TIPO = CLIENTES_TIPOS.CHAVE AND
            NOTAS.CHAVE = NOTAS_PESO_LIQUIDO.CHAVE_NOTA(+) AND
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
            CLIENTES.CHAVE_GRUPOECONOMICO = GRUPO_ECONOMICO.CHAVE AND
            NOTAS.VALOR_COMERCIAL = 'SIM' AND

            {grupo_economico_pesquisa}
            {carteira_pesquisa}
            {tipo_cliente_pesquisa}
            {produto_pesquisa}

            NOTAS.DATA_EMISSAO >= :data_inicio AND
            NOTAS.DATA_EMISSAO <= :data_fim

        GROUP BY
            {carteira_campo}
            {grupo_economico_campo}
            {tipo_cliente_campo}
            {produto_campo}
            1

        ORDER BY
            {carteira_campo}
            {tipo_cliente_campo}
            {produto_campo}
            VALOR_MERCADORIAS DESC
    """

    sql = sql.format(**kwargs_sql)

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, data_fim=data_fim, **kwargs_ora)

    return resultado
