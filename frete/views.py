from typing import Dict
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import ListView
from django.http import HttpResponse
from frete.services import calcular_frete, get_prazos, get_dados_notas, get_dados_notas_monitoramento
from frete.forms import PesquisarOrcamentoFreteForm, PesquisarCidadePrazosForm, PeriodoInicioFimForm
from home.models import Produtos
from utils.site_setup import get_transportadoras_regioes_valores
from utils.base_forms import FormPesquisarMixIn
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario
from utils.converter import converter_datetime_para_str_ddmmyy, converter_datetime_para_str_ddmmyyyy
from pandas import offsets


def calculo_frete(request):
    titulo_pagina = 'Frete - Calculo de Frete'

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
    titulo_pagina = 'Frete - Prazos'

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


class MedidasProdutos(ListView):
    model = Produtos
    template_name = 'frete/pages/medidas-produtos.html'
    context_object_name = 'medidas_produtos'
    ordering = 'nome',
    queryset = Produtos.filter_ativos()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'titulo_pagina': 'Frete - Medidas Produtos'})

        if self.request.GET:
            formulario = FormPesquisarMixIn(self.request.GET)
            context.update({'formulario': formulario})
        else:
            context.update({'formulario': FormPesquisarMixIn()})

        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.GET:
            queryset = queryset.none()
            return queryset

        formulario = FormPesquisarMixIn(self.request.GET)

        if formulario.is_valid() and self.request.GET:
            produto = formulario.cleaned_data.get('pesquisar')
            if produto:
                queryset = queryset.filter(nome__icontains=produto)

        return queryset


@user_passes_test(lambda usuario: usuario.has_perm('frete.view_transportadorasregioesvalores'), login_url='/admin/login/')
def relatorios(request):
    titulo_pagina = 'Frete - Relatorios'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    if request.method == 'GET' and request.GET:
        formulario = PeriodoInicioFimForm(request.GET)
        contexto.update({'formulario': formulario})

        if formulario.is_valid():
            data_inicio = formulario.cleaned_data.get('inicio')
            data_fim = formulario.cleaned_data.get('fim')

            if 'agili-submit' in request.GET:

                agili = get_transportadoras_regioes_valores().filter(
                    transportadora_origem_destino__transportadora__nome__iexact='agili',
                    transportadora_origem_destino__estado_origem_destino__uf_origem__sigla='SP',
                    transportadora_origem_destino__estado_origem_destino__uf_destino__sigla='SP',
                    descricao__iexact='capital',
                ).first()
                notas = get_dados_notas(data_inicio, data_fim)

                for nota in notas:
                    valor_calculo_frete, *_ = calcular_frete(nota['ORCAMENTO'],
                                                             transportadora_regiao_valor_especifico=agili)
                    nota.update({'VALOR_CALCULO_FRETE': valor_calculo_frete[0]['valor_frete_empresa']})

                excel = arquivo_excel(notas)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'relatorio_agili'

            if 'rastreamento-submit' in request.GET:

                notas = get_dados_notas_monitoramento(data_inicio, data_fim)

                for nota in notas:
                    despacho = nota['DATA_DESPACHO']
                    nota.update({'DATA_DESPACHO': converter_datetime_para_str_ddmmyyyy(nota['DATA_DESPACHO']), })
                    try:
                        valor_calculo_frete, * _ = calcular_frete(nota['ORCAMENTO'],
                                                                  transportadora_orcamento_pedido=True)
                        prazo = valor_calculo_frete[0]['prazo']
                        prazo_entrega = despacho + offsets.BDay(prazo)
                        nota.update({
                            'PRAZO_ENTREGA': converter_datetime_para_str_ddmmyy(prazo_entrega),
                            'PRAZO': prazo,
                        })
                    except ObjectDoesNotExist:
                        nota.update({'PRAZO_ENTREGA': '', 'PRAZO': '', })

                excel = arquivo_excel(notas)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'relatorio_rastreamento'

            response = HttpResponse(
                arquivo,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(nome_arquivo)
            return response

    contexto.update({'formulario': PeriodoInicioFimForm()})

    return render(request, 'frete/pages/relatorios.html', contexto)
