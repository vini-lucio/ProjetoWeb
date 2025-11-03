from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from rh.models import Funcionarios, Ferias, Dependentes
from rh.forms import ReciboValeTransporteForm, FeriasEmAbertoForm, DependentesIrForm
from rh_relatorios.models import FuncionariosSalarioFuncaoAtual


@user_passes_test(lambda usuario: usuario.has_perm('rh.view_funcionarios'), login_url='/admin/login/')
def index(request):
    """Retorna pagina principal do app de RH.
    É necessario ter o direito de visualizar funcionarios."""
    titulo_pagina = 'RH'
    return render(request, 'rh/pages/index.html', {'titulo_pagina': titulo_pagina})


@method_decorator(user_passes_test(lambda usuario: usuario.has_perm('rh.view_valetransportesfuncionarios'), login_url='/admin/login/'), name='dispatch')
class ReciboValeTransporteListView(ListView):
    """Retorna dados de vale transporte por funcionario para pagina de relatorio de recibo de vale transporte
    de acordo com o formulario.
    É necessario ter o direito de visualizar vale transportes funcionarios"""
    model = Funcionarios
    template_name = 'rh/pages/recibo-vale-transporte.html'
    context_object_name = 'recibos_vale_transporte'
    ordering = 'job__descricao', 'nome',
    queryset = Funcionarios.filter_ativos()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'RH - Recibo Vale Transporte'})

        if self.request.GET:
            formulario = ReciboValeTransporteForm(self.request.GET)
            context.update({'formulario': formulario})
            if formulario.is_valid():
                context.update({'data_inicio': formulario.cleaned_data.get('inicio')})
                context.update({'data_fim': formulario.cleaned_data.get('fim')})
                context.update({'data_assinatura': formulario.cleaned_data.get('assinatura')})
        else:
            context.update({'formulario': ReciboValeTransporteForm()})

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.GET:
            queryset = queryset.none()
            return queryset

        formulario = ReciboValeTransporteForm(self.request.GET)

        if formulario.is_valid() and self.request.GET:
            job = formulario.cleaned_data.get('job')
            if job:
                queryset = queryset.filter(job=job)

        return queryset


@method_decorator(user_passes_test(lambda usuario: usuario.has_perm('rh.view_ferias'), login_url='/admin/login/'), name='dispatch')
class FeriasEmAbertoListView(ListView):
    """Retorna dados para pagina de relatorio de ferias em aberto de acordo com o formulario.
    É necessario ter o direito de visualizar ferias"""
    model = Ferias
    template_name = 'rh/pages/ferias-em-aberto.html'
    context_object_name = 'ferias_em_aberto'
    ordering = 'funcionario__nome',
    queryset = Ferias.filter_em_aberto()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'RH - Ferias Em Aberto'})

        if self.request.GET:
            formulario = FeriasEmAbertoForm(self.request.GET)
            context.update({'formulario': formulario})
        else:
            context.update({'formulario': FeriasEmAbertoForm()})

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.GET:
            queryset = queryset.none()
            return queryset

        formulario = FeriasEmAbertoForm(self.request.GET)

        if formulario.is_valid() and self.request.GET:
            job = formulario.cleaned_data.get('job')
            setor = formulario.cleaned_data.get('setor')
            if job and setor:
                salarios = FuncionariosSalarioFuncaoAtual.objects.filter(job=job.descricao, setor=setor.descricao)
                queryset = queryset.filter(funcionario__in=[salario.funcionario for salario in salarios])

        return queryset


@method_decorator(user_passes_test(lambda usuario: usuario.has_perm('rh.view_ferias'), login_url='/admin/login/'), name='dispatch')
class SolicitacaoFeriasDetailView(DetailView):
    """Retorna dados de uma ferias para pagina de relatorio de solicitção de ferias.
    É necessario ter o direito de visualizar ferias."""
    model = Ferias
    template_name = 'rh/pages/solicitacao-ferias.html'
    context_object_name = 'solicitacao_ferias'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        titulo_pagina = f'{self.get_object().funcionario.nome}'  # type: ignore
        context.update({'titulo_pagina': f'RH - Solicitação de Ferias {titulo_pagina}'})
        return context


@method_decorator(user_passes_test(lambda usuario: usuario.has_perm('rh.view_dependentes'), login_url='/admin/login/'), name='dispatch')
class DependentesIrListView(ListView):
    """Retorna dados de dependentes por funcionario para pagina de relatorio de dependentes IR de acordo com o formulario.
    É necessario ter o direito de visualizar dependentes."""
    model = Funcionarios
    template_name = 'rh/pages/dependentes-ir.html'
    context_object_name = 'dependentes_ir'
    ordering = 'job__descricao', 'nome',
    queryset = Funcionarios.filter_ativos()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'RH - Dependentes IR'})

        if self.request.GET:
            formulario = DependentesIrForm(self.request.GET)
            context.update({'formulario': formulario})
            if formulario.is_valid():
                context.update({'data_assinatura': formulario.cleaned_data.get('assinatura')})
        else:
            context.update({'formulario': DependentesIrForm()})

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.GET:
            queryset = queryset.none()
            return queryset

        formulario = DependentesIrForm(self.request.GET)

        if formulario.is_valid() and self.request.GET:
            job = formulario.cleaned_data.get('job')
            if job:
                queryset = queryset.filter(job=job)
                dependentes_ir = Dependentes.filter_dependente_ir()
                queryset = queryset.filter(dependentes__in=[dependente for dependente in dependentes_ir]).distinct()

        return queryset
