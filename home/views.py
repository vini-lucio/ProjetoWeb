from django.shortcuts import render
from django.views.generic import ListView, DetailView
from home.models import HomeLinks


class IndexListView(ListView):
    model = HomeLinks
    template_name = 'home/pages/index.html'
    context_object_name = 'home_links'
    ordering = 'tamanho_botao', 'ordem', 'id',
    queryset = HomeLinks.objects.filter(visivel=True)


class HomeLinkDetailView(DetailView):
    model = HomeLinks
    template_name = 'home/pages/pagina.html'
    context_object_name = 'home_link'

    def get_queryset(self):
        return super().get_queryset().filter(visivel=True)


class ConsultoriaVendasListView(ListView):
    model = HomeLinks
    template_name = 'home/pages/consultoria-vendas.html'
    context_object_name = 'home_links'
    ordering = 'ordem', 'id',
    queryset = HomeLinks.objects.filter(visivel=True, tamanho_botao='consultoria')


def calculo_piso_elevado(request):
    return render(request, 'home/pages/calculo-piso-elevado.html')


def calculo_quimicos(request):
    return render(request, 'home/pages/calculo-quimicos.html')


def calculo_niveladores(request):
    return render(request, 'home/pages/calculo-niveladores.html')
