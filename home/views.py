from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.views.generic import ListView, DetailView
from home.models import HomeLinks
from django.db.models import Q
from .services import get_tabela_precos, migrar_cidades  # , totalizar_funcionarios_mes
from .forms import ConfirmacaoMigrarCidades
from django.contrib.auth.decorators import user_passes_test


@user_passes_test(lambda usuario: usuario.is_superuser, login_url='/admin/login/')
def migracao(request):
    titulo_pagina = 'Migração'

    if request.method == 'POST':
        formulario = ConfirmacaoMigrarCidades(request.POST)
        if formulario.is_valid() and formulario.cleaned_data['confirma']:
            migrar_cidades()
            messages.success(request, "Migração de cidades concluída!")
            return redirect(reverse('home:migracao'))

    formulario = ConfirmacaoMigrarCidades()

    contexto = {'titulo_pagina': titulo_pagina, 'formulario': formulario, }

    # totalizar_funcionarios_mes(11, 2024)

    return render(request, 'home/pages/migracao.html', contexto)


class IndexListView(ListView):
    model = HomeLinks
    template_name = 'home/pages/index.html'
    context_object_name = 'home_links'
    ordering = 'tamanho_botao', 'ordem', 'id',
    queryset = HomeLinks.objects.filter(visivel=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'Home'})
        return context


class HomeLinkDetailView(DetailView):
    model = HomeLinks
    template_name = 'home/pages/pagina.html'
    context_object_name = 'home_link'

    def get_queryset(self):
        return super().get_queryset().filter(visivel=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titulo_pagina = f'{self.get_object().titulo}'  # type: ignore
        context.update({'titulo_pagina': titulo_pagina})
        return context


class ConsultoriaVendasListView(ListView):
    model = HomeLinks
    template_name = 'home/pages/consultoria-vendas.html'
    context_object_name = 'home_links'
    ordering = 'ordem', 'id',
    queryset = HomeLinks.objects.filter(visivel=True).filter(
        Q(tamanho_botao='consultoria') | Q(url_externo='consultoria-vendas/'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'Consultoria de Vendas'})
        return context


def calculo_piso_elevado(request):
    titulo_pagina = 'Calculo Piso Elevado'
    return render(request, 'home/pages/calculo-piso-elevado.html', {'titulo_pagina': titulo_pagina})


def calculo_quimicos(request):
    titulo_pagina = 'Calculo Quimicos'
    return render(request, 'home/pages/calculo-quimicos.html', {'titulo_pagina': titulo_pagina})


def calculo_niveladores(request):
    titulo_pagina = 'Calculo Niveladores de Piso'
    return render(request, 'home/pages/calculo-niveladores.html', {'titulo_pagina': titulo_pagina})


def tabela_precos(request):
    titulo_pagina = 'Tabela de Preços'

    tabela = get_tabela_precos()

    contexto = {'titulo_pagina': titulo_pagina, 'tabela': tabela}

    return render(request, 'home/pages/tabela-precos.html', contexto)
