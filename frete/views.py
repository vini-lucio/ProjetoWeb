from typing import Dict
from django.shortcuts import render
from frete.services import calcular_frete
from frete.forms import PesquisarOrcamentoFrete


def calculo_frete(request):
    titulo_pagina = 'Calculo de Frete'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    if request.method == 'GET' and request.GET:
        formulario = PesquisarOrcamentoFrete(request.GET)
        if formulario.is_valid():
            orcamento: int = formulario.cleaned_data.get('orcamento')  # type:ignore
            zona_rural: bool = True if formulario.cleaned_data.get('zona_rural') == 'sim' else False  # type:ignore

            fretes, dados_orcamento, dados_itens_orcamento, dados_volumes = calcular_frete(orcamento, zona_rural)

            contexto.update({'dados_orcamento': dados_orcamento})
            contexto.update({'dados_volumes': dados_volumes})
            contexto.update({'dados_itens_orcamento': dados_itens_orcamento})
            contexto.update({'fretes': fretes})
    else:
        formulario = PesquisarOrcamentoFrete()

    contexto.update({'formulario': formulario})

    return render(request, 'frete/pages/calculo-frete.html', contexto)
