from typing import Dict
from django.shortcuts import render
from django.http import HttpResponse
from .services import DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_supervisao
from .forms import RelatoriosSupervisaoFaturamentosForm, RelatoriosSupervisaoOrcamentosForm
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario, arquivo_excel_response


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    dashboard_vendas_tv = DashboardVendasTv()
    dados = dashboard_vendas_tv.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)


def vendas_supervisao(request):
    titulo_pagina = 'Dashboard Vendas - Supervisão'

    dashboard_vendas_supervisao = DashboardVendasSupervisao()
    dados = dashboard_vendas_supervisao.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-supervisao.html', contexto)


def relatorios_supervisao(request, fonte: str):
    fonte_relatorio = fonte
    if fonte_relatorio not in ('faturamentos', 'orcamentos'):
        return HttpResponse("Pagina invalida", status=404)

    orcamento = False
    if fonte_relatorio == 'orcamentos':
        orcamento = True

    titulo_pagina = 'Dashboard Vendas - Relatorios Supervisão'

    titulo_pagina_2 = 'Relatorios Faturamentos'
    if orcamento:
        titulo_pagina_2 = 'Relatorios Orçamentos'

    contexto: Dict = {'titulo_pagina': titulo_pagina, 'titulo_pagina_2': titulo_pagina_2,
                      'fonte_relatorio': fonte_relatorio}

    form = RelatoriosSupervisaoFaturamentosForm
    if orcamento:
        form = RelatoriosSupervisaoOrcamentosForm

    formulario = form()

    if request.method == 'GET' and request.GET:
        formulario = form(request.GET)
        if formulario.is_valid():
            if request.GET:
                dados = get_relatorios_supervisao(orcamento, **formulario.cleaned_data)

                coluna_rentabilidade = formulario.cleaned_data.get('coluna_rentabilidade')
                coluna_rentabilidade_valor = formulario.cleaned_data.get('coluna_rentabilidade_valor')
                coluna_quantidade_documentos = formulario.cleaned_data.get('coluna_quantidade_documentos')

                valor_mercadorias_total = 0
                mc_total = 0
                mc_valor_total = 0
                quantidade_documentos_total = 0
                for dado in dados:
                    valor_mercadorias_total += dado.get('VALOR_MERCADORIAS')
                    if coluna_rentabilidade or coluna_rentabilidade_valor:
                        mc_valor_total += dado.get('MC_VALOR')
                    if coluna_quantidade_documentos:
                        quantidade_documentos_total += dado.get('QUANTIDADE_DOCUMENTOS')
                if mc_valor_total and valor_mercadorias_total:
                    mc_total = mc_valor_total / valor_mercadorias_total * 100

                contexto.update({
                    'dados': dados,
                    'valor_mercadorias_total': valor_mercadorias_total,
                    'mc_total': mc_total,
                    'mc_valor_total': mc_valor_total,
                    'quantidade_documentos_total': quantidade_documentos_total,
                })

            if 'exportar-submit' in request.GET:
                # TODO: botão para exportar com base de email
                excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'relatorio_faturamentos'
                if orcamento:
                    nome_arquivo = 'relatorio_orcamentos'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

    contexto.update({'formulario': formulario, })

    return render(request, 'dashboards/pages/relatorios-supervisao.html', contexto)
