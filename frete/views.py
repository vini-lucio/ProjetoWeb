from django.shortcuts import render


def calculo_frete(request):
    titulo_pagina = 'Calculo de Frete'
    return render(request, 'frete/pages/index.html', {'titulo_pagina': titulo_pagina})
