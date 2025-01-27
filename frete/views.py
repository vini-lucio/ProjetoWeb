from typing import Dict
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from frete.services import calcular_frete, get_prazos
from frete.forms import PesquisarOrcamentoFreteForm, PesquisarCidadePrazosForm


def calculo_frete(request):
    titulo_pagina = 'Calculo de Frete'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    if request.method == 'GET' and request.GET:
        formulario = PesquisarOrcamentoFreteForm(request.GET)
        if formulario.is_valid():
            orcamento: int = formulario.cleaned_data.get('orcamento')  # type:ignore
            zona_rural: bool = True if formulario.cleaned_data.get('zona_rural') == 'sim' else False  # type:ignore

            try:
                fretes, dados_orcamento, dados_itens_orcamento, dados_volumes = calcular_frete(orcamento, zona_rural)
                contexto.update({'dados_orcamento': dados_orcamento})
                contexto.update({'dados_volumes': dados_volumes})
                contexto.update({'dados_itens_orcamento': dados_itens_orcamento})
                contexto.update({'fretes': fretes})
            except ObjectDoesNotExist as erros:
                contexto.update({'erros': erros})

    formulario = PesquisarOrcamentoFreteForm()

    contexto.update({'formulario': formulario})

    return render(request, 'frete/pages/calculo-frete.html', contexto)


def prazos(request):
    titulo_pagina = 'Prazos'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    if request.method == 'GET' and request.GET:
        formulario = PesquisarCidadePrazosForm(request.GET)
        if formulario.is_valid():
            uf_origem = formulario.cleaned_data.get('uf_origem').sigla  # type:ignore
            uf_destino = formulario.cleaned_data.get('uf_destino').sigla  # type:ignore
            cidade_destino: str = formulario.cleaned_data.get('cidade_destino').upper()  # type:ignore
            try:
                prazos = get_prazos(uf_origem, uf_destino, cidade_destino)
                contexto.update({'prazos': prazos})
            except ObjectDoesNotExist as erros:
                contexto.update({'erros': erros})
    else:
        formulario = PesquisarCidadePrazosForm()

    contexto.update({'formulario': formulario})

    return render(request, 'frete/pages/prazos.html', contexto)
