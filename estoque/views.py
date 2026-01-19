from typing import Dict
from django.shortcuts import render
from django.db.models import Q
from .models import ProdutosPallets
from utils.base_forms import FormPesquisarMixIn


def estoque(request):
    """Retorna pagina de estoque"""
    titulo_pagina = 'Estoque'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormPesquisarMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormPesquisarMixIn(request.GET)
        dados = []

        if formulario.is_valid():
            pesquisar = formulario.cleaned_data.get('pesquisar')
            dados = ProdutosPallets.objects.filter(
                Q(produto__nome__icontains=pesquisar) |
                Q(pallet__endereco__nome__icontains=pesquisar) |
                Q(fornecedor__sigla__iexact=pesquisar) |
                Q(lote_fornecedor__iexact=pesquisar)
            )

        contexto.update({'dados': dados, })

    contexto.update({'formulario': formulario, })

    return render(request, 'estoque/pages/estoque.html', contexto)
