from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.views.generic import ListView, DetailView
from home.models import HomeLinks, ProdutosModelos
from home.forms import PesquisarForm
from django.db.models import Q
from django.utils.text import slugify
from .services import get_tabela_precos, migrar_cidades, migrar_unidades
from .forms import ConfirmacaoMigrar
from django.contrib.auth.decorators import user_passes_test
from collections import Counter


@user_passes_test(lambda usuario: usuario.is_superuser, login_url='/admin/login/')
def migracao(request):
    titulo_pagina = 'Migração'
    id_confirma_cidades = 'confirma-migrar-cidades'
    id_confirma_unidades = 'confirma-migrar-unidades'

    if request.method == 'POST':
        if 'cidades-submit' in request.POST:
            formulario_migrar_cidades = ConfirmacaoMigrar(request.POST, id_confirma=id_confirma_cidades)
            if formulario_migrar_cidades.is_valid() and formulario_migrar_cidades.cleaned_data['confirma']:
                migrar_cidades()
                mensagem = "Migração de cidades concluída!"
                extra_tags = 'cidades'

        elif 'unidades-submit' in request.POST:
            formulario_migrar_unidades = ConfirmacaoMigrar(request.POST, id_confirma=id_confirma_unidades)
            if formulario_migrar_unidades.is_valid() and formulario_migrar_unidades.cleaned_data['confirma']:
                migrar_unidades()
                mensagem = "Migração de unidades concluída!"
                extra_tags = 'unidades'

        messages.success(request, mensagem, extra_tags=extra_tags)
        return redirect(reverse('home:migracao'))

    formulario_migrar_cidades = ConfirmacaoMigrar(id_confirma=id_confirma_cidades)
    formulario_migrar_unidades = ConfirmacaoMigrar(id_confirma=id_confirma_unidades)

    contexto = {
        'titulo_pagina': titulo_pagina,
        'formulario_migrar_cidades': formulario_migrar_cidades,
        'formulario_migrar_unidades': formulario_migrar_unidades,
    }

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


class ProdutosModelosListView(ListView):
    model = ProdutosModelos
    template_name = 'home/pages/produtos_modelos.html'
    context_object_name = 'produtos_modelos'
    ordering = 'id',

    def get_queryset(self):
        queryset = super().get_queryset().order_by('descricao')
        resultado = queryset

        if not self.request.GET:
            queryset = queryset.none()
            return queryset

        formulario = PesquisarForm(self.request.GET)

        if formulario.is_valid() and self.request.GET:
            pesquisar = formulario.cleaned_data.get('pesquisar')
            if pesquisar:
                pesquisar = slugify(pesquisar)
                resultado = queryset.filter(slug=pesquisar)
                if not resultado.first():
                    resultado = queryset.filter(tags__slug=pesquisar)
                    if not resultado.first():
                        resultado = queryset.filter(tags__slug__icontains=pesquisar)

        return resultado

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'Produtos Modelos'})

        if self.request.GET:
            formulario = PesquisarForm(self.request.GET)
        else:
            formulario = PesquisarForm()

        context.update({'formulario': formulario})
        return context


class ProdutosModelosDetailView(DetailView):
    model = ProdutosModelos
    template_name = 'home/pages/produtos_modelo.html'
    context_object_name = 'produtos_modelo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titulo_pagina = f'{self.get_object().descricao}'  # type: ignore

        modelo = self.get_object()
        tags = modelo.tags.all()  # type: ignore

        sugestoes = []
        for tag in tags:
            modelos_com_tag = ProdutosModelos.objects.filter(tags=tag).exclude(pk=modelo.pk)
            [sugestoes.append(modelo) for modelo in modelos_com_tag]
        contagem = Counter(sugestoes).most_common()

        sugestoes_ordenadas = []
        for modelo, tags_encontradas in contagem:
            sugestoes_ordenadas.append(modelo)

        context.update({'titulo_pagina': titulo_pagina, 'sugestoes': sugestoes_ordenadas})
        return context
