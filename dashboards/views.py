from django.shortcuts import render
from .services import (pedidos_dia, conversao_de_orcamentos, pedidos_mes, rentabilidade_pedidos_dia,
                       rentabilidade_pedidos_mes, confere_pedidos)
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import get_site_setup


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    SITE_SETUP = get_site_setup()
    if SITE_SETUP:
        META_DIARIA = SITE_SETUP.meta_diaria_as_float
        META_MES = SITE_SETUP.meta_mes_as_float
        PRIMEIRO_DIA_MES = SITE_SETUP.primeiro_dia_mes_as_ddmmyyyy
        PRIMEIRO_DIA_UTIL_MES = SITE_SETUP.primeiro_dia_util_mes_as_ddmmyyyy
        ULTIMO_DIA_MES = SITE_SETUP.ultimo_dia_mes_as_ddmmyyyy
        PRIMEIRO_DIA_UTIL_PROXIMO_MES = SITE_SETUP.primeiro_dia_util_proximo_mes_as_ddmmyyyy
        DESPESA_ADMINISTRATIVA_FIXA = SITE_SETUP.despesa_administrativa_fixa_as_float

    PEDIDOS_DIA = pedidos_dia(PRIMEIRO_DIA_UTIL_PROXIMO_MES)
    PORCENTAGEM_META_DIA = int(PEDIDOS_DIA / META_DIARIA * 100)
    FALTAM_META_DIA = round(META_DIARIA - PEDIDOS_DIA, 2)
    CONVERSAO_DE_ORCAMENTOS = conversao_de_orcamentos()
    FALTAM_ABRIR_ORCAMENTOS_DIA = round(FALTAM_META_DIA / (CONVERSAO_DE_ORCAMENTOS / 100), 2)
    PEDIDOS_MES = pedidos_mes(PRIMEIRO_DIA_MES, PRIMEIRO_DIA_UTIL_MES, ULTIMO_DIA_MES, PRIMEIRO_DIA_UTIL_PROXIMO_MES)
    PORCENTAGEM_META_MES = int(PEDIDOS_MES / META_MES * 100)
    FALTAM_META_MES = round(META_MES - PEDIDOS_MES, 2)

    RENTABILIDADE_PEDIDOS_DIA = rentabilidade_pedidos_dia(DESPESA_ADMINISTRATIVA_FIXA, PRIMEIRO_DIA_UTIL_PROXIMO_MES)
    COR_RENTABILIDADE_PEDIDOS_DIA = cor_rentabilidade_css(RENTABILIDADE_PEDIDOS_DIA)

    RENTABILIDADE_PEDIDOS_MES = rentabilidade_pedidos_mes(DESPESA_ADMINISTRATIVA_FIXA, PRIMEIRO_DIA_MES,
                                                          PRIMEIRO_DIA_UTIL_MES, ULTIMO_DIA_MES,
                                                          PRIMEIRO_DIA_UTIL_PROXIMO_MES)
    RENTABILIDADE_PEDIDOS_MES_MC_MES = RENTABILIDADE_PEDIDOS_MES['mc_mes']
    RENTABILIDADE_PEDIDOS_MES_TOTAL_MES_SEM_CONVERTER_MOEDA = RENTABILIDADE_PEDIDOS_MES['total_mes_sem_converter_moeda']
    RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE = RENTABILIDADE_PEDIDOS_MES['rentabilidade_mes']
    COR_RENTABILIDADE_PEDIDOS_MES = cor_rentabilidade_css(RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE)

    FALTA_MUDAR_COR_MES = falta_mudar_cor_mes(
        RENTABILIDADE_PEDIDOS_MES_MC_MES,
        RENTABILIDADE_PEDIDOS_MES_TOTAL_MES_SEM_CONVERTER_MOEDA,
        RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE
    )
    FALTA_MUDAR_COR_MES_VALOR = round(FALTA_MUDAR_COR_MES[0], 2)
    FALTA_MUDAR_COR_MES_VALOR_RENTABILIDADE = round(FALTA_MUDAR_COR_MES[1], 2)
    FALTA_MUDAR_COR_MES_PORCENTAGEM = round(FALTA_MUDAR_COR_MES[2], 2)
    FALTA_MUDAR_COR_MES_COR = FALTA_MUDAR_COR_MES[3]

    DATA_HORA_ATUAL = data_hora_atual()

    CONFERE_PEDIDOS = confere_pedidos()

    # TODO: separar codigo SQL em comum (LFRETE interno, por exemplo)

    dados = {
        'meta_diaria': META_DIARIA,
        'pedidos_dia': PEDIDOS_DIA,
        'porcentagem_meta_dia': PORCENTAGEM_META_DIA,
        'faltam_meta_dia': FALTAM_META_DIA,
        'conversao_de_orcamentos': CONVERSAO_DE_ORCAMENTOS,
        'faltam_abrir_orcamentos_dia': FALTAM_ABRIR_ORCAMENTOS_DIA,
        'meta_mes': META_MES,
        'pedidos_mes': PEDIDOS_MES,
        'porcentagem_meta_mes': PORCENTAGEM_META_MES,
        'faltam_meta_mes': FALTAM_META_MES,
        'data_hora_atual': DATA_HORA_ATUAL,
        'rentabilidade_pedidos_dia': RENTABILIDADE_PEDIDOS_DIA,
        'cor_rentabilidade_css_dia': COR_RENTABILIDADE_PEDIDOS_DIA,
        'rentabilidade_pedidos_mes_rentabilidade_mes': RENTABILIDADE_PEDIDOS_MES_RENTABILIDADE,
        'cor_rentabilidade_css_mes': COR_RENTABILIDADE_PEDIDOS_MES,
        'falta_mudar_cor_mes_valor': FALTA_MUDAR_COR_MES_VALOR,
        'falta_mudar_cor_mes_valor_rentabilidade': FALTA_MUDAR_COR_MES_VALOR_RENTABILIDADE,
        'falta_mudar_cor_mes_porcentagem': FALTA_MUDAR_COR_MES_PORCENTAGEM,
        'falta_mudar_cor_mes_cor': FALTA_MUDAR_COR_MES_COR,
        'confere_pedidos': CONFERE_PEDIDOS,
    }

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)
