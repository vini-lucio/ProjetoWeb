from django.shortcuts import render


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'
    return render(request, 'dashboards/pages/vendas-tv.html', {'titulo_pagina': titulo_pagina})
