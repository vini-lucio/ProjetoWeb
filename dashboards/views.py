from django.shortcuts import render
from .services import pedidos_dia, conversao_de_orcamentos, pedidos_mes


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
    PORCENTAGEM_META_MES = round(PEDIDOS_MES / META_MES * 100, 2)
    FALTAM_META_MES = round(META_MES - PEDIDOS_MES, 2)

    # TODO: confere pedido
    # TODO: cores rentabilidade (dia, mes, quanto falta para mudar de cor (valor e porcentagem))

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
    }

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)
