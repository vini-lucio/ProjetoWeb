from django.shortcuts import render
from .services import teste


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'
    titulo_pagina = teste()
    return render(request, 'dashboards/pages/vendas-tv.html', {'titulo_pagina': titulo_pagina})
