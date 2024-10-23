from django.shortcuts import render
from .services import (pedidos_dia, conversao_de_orcamentos, pedidos_mes, rentabilidade_pedidos_dia,
                       rentabilidade_pedidos_mes)
from utils.data_hora_atual import data_hora_atual
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    META_DIARIA = 165217.39
    PEDIDOS_DIA = pedidos_dia()
    PORCENTAGEM_META_DIA = int(PEDIDOS_DIA / META_DIARIA * 100)
    FALTAM_META_DIA = round(META_DIARIA - PEDIDOS_DIA, 2)
    CONVERSAO_DE_ORCAMENTOS = conversao_de_orcamentos()
    FALTAM_ABRIR_ORCAMENTOS_DIA = round(FALTAM_META_DIA / (CONVERSAO_DE_ORCAMENTOS / 100), 2)
    META_MES = 3800000.0
    PEDIDOS_MES = pedidos_mes()
    PORCENTAGEM_META_MES = int(PEDIDOS_MES / META_MES * 100)
    FALTAM_META_MES = round(META_MES - PEDIDOS_MES, 2)

    RENTABILIDADE_PEDIDOS_DIA = rentabilidade_pedidos_dia()
    COR_RENTABILIDADE_PEDIDOS_DIA = cor_rentabilidade_css(RENTABILIDADE_PEDIDOS_DIA)

    RENTABILIDADE_PEDIDOS_MES = rentabilidade_pedidos_mes()
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

    # TODO: confere pedido
    # TODO: tabela de parametros com as datas, despesa fixa meta total, etc
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
    }

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)
