from django.shortcuts import render
from .services import DashboardVendasTv, DashboardVendasSupervisao


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    dashboard_vendas_tv = DashboardVendasTv()
    dados = dashboard_vendas_tv.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)


def vendas_supervisao(request):
    titulo_pagina = 'Dashboard Vendas - Supervisão'

    dashboard_vendas_supervisao = DashboardVendasSupervisao()
    dados = dashboard_vendas_supervisao.get_dados()

    # TODO: atalhos de relatorios???

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-supervisao.html', contexto)
