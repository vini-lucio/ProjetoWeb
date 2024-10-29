from django.shortcuts import render
from .services import (pedidos_dia, conversao_de_orcamentos, pedidos_mes, rentabilidade_pedidos_dia,
                       rentabilidade_pedidos_mes, confere_pedidos)
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda


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

        self.PEDIDOS_DIA = pedidos_dia(self.PRIMEIRO_DIA_UTIL_PROXIMO_MES)
        self.PORCENTAGEM_META_DIA = int(self.PEDIDOS_DIA / self.META_DIARIA * 100)
        self.FALTAM_META_DIA = round(self.META_DIARIA - self.PEDIDOS_DIA, 2)
        self.CONVERSAO_DE_ORCAMENTOS = conversao_de_orcamentos()
        self.FALTAM_ABRIR_ORCAMENTOS_DIA = round(self.FALTAM_META_DIA / (self.CONVERSAO_DE_ORCAMENTOS / 100), 2)
        self.PEDIDOS_MES = pedidos_mes(self.PRIMEIRO_DIA_MES, self.PRIMEIRO_DIA_UTIL_MES,
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
            'porcentagem_meta_dia': self.PORCENTAGEM_META_DIA,
            'faltam_meta_dia': self.FALTAM_META_DIA,
            'conversao_de_orcamentos': self.CONVERSAO_DE_ORCAMENTOS,
            'faltam_abrir_orcamentos_dia': self.FALTAM_ABRIR_ORCAMENTOS_DIA,
            'meta_mes': self.META_MES,
            'pedidos_mes': self.PEDIDOS_MES,
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


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    dashboard_vendas_tv = DashboardVendasTv()
    dados = dashboard_vendas_tv.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)
