from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from rh.models import Funcionarios, Ferias
from rh.forms import ReciboValeTransporteForm, FeriasEmAbertoForm
from rh_relatorios.models import FuncionariosSalarioFuncaoAtual


@login_required(login_url='/admin/login/')
def index(request):
    titulo_pagina = 'RH'
    return render(request, 'rh/pages/index.html', {'titulo_pagina': titulo_pagina})


@method_decorator(user_passes_test(lambda usuario: usuario.has_perm('rh.view_valetransportesfuncionarios'), login_url='/admin/login/'), name='dispatch')
class ReciboValeTransporteListView(ListView):
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
    model = Ferias
    template_name = 'rh/pages/ferias-em-aberto.html'
    context_object_name = 'ferias_em_aberto'
    ordering = 'funcionario',
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
