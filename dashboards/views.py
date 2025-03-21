from typing import Dict
from django.http import HttpResponse
from django.shortcuts import render
from .services import DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_supervisao
from .forms import RelatoriosSupervisaoForm
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario


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


def relatorios_supervisao(request):
    titulo_pagina = 'Dashboard Vendas - Relatorios Supervisão'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    formulario = RelatoriosSupervisaoForm()

    if request.method == 'GET' and request.GET:
        formulario = RelatoriosSupervisaoForm(request.GET)
        if formulario.is_valid():
            if request.GET:
                data_inicio = formulario.cleaned_data.get('inicio')
                data_fim = formulario.cleaned_data.get('fim')

                coluna_carteira = formulario.cleaned_data.get('coluna_carteira')
                carteira = formulario.cleaned_data.get('carteira')
                chave_carteira = carteira.pk if carteira else None

                coluna_grupo_economico = formulario.cleaned_data.get('coluna_grupo_economico')
                grupo_economico = formulario.cleaned_data.get('grupo_economico')

                coluna_tipo_cliente = formulario.cleaned_data.get('coluna_tipo_cliente')
                tipo_cliente = formulario.cleaned_data.get('tipo_cliente')
                chave_tipo_cliente = tipo_cliente.pk if tipo_cliente else None

                coluna_familia_produto = formulario.cleaned_data.get('coluna_familia_produto')
                familia_produto = formulario.cleaned_data.get('familia_produto')
                chave_familia_produto = familia_produto.pk if familia_produto else None

                coluna_produto = formulario.cleaned_data.get('coluna_produto')
                produto = formulario.cleaned_data.get('produto')

                coluna_unidade = formulario.cleaned_data.get('coluna_unidade')

                coluna_preco_tabela_inclusao = formulario.cleaned_data.get('coluna_preco_tabela_inclusao')

                coluna_preco_venda_medio = formulario.cleaned_data.get('coluna_preco_venda_medio')

                coluna_quantidade = formulario.cleaned_data.get('coluna_quantidade')

                coluna_cidade = formulario.cleaned_data.get('coluna_cidade')
                cidade = formulario.cleaned_data.get('cidade')

                coluna_estado = formulario.cleaned_data.get('coluna_estado')
                estado = formulario.cleaned_data.get('estado')
                chave_estado = estado.pk if estado else None

                nao_compraram_depois = formulario.cleaned_data.get('nao_compraram_depois')

                coluna_rentabilidade = formulario.cleaned_data.get('coluna_rentabilidade')

                coluna_rentabilidade_valor = formulario.cleaned_data.get('coluna_rentabilidade_valor')

                dados = get_relatorios_supervisao(
                    data_inicio, data_fim,
                    coluna_grupo_economico, grupo_economico,  # type:ignore
                    coluna_carteira, chave_carteira,  # type:ignore
                    coluna_tipo_cliente, chave_tipo_cliente,  # type:ignore
                    coluna_familia_produto, chave_familia_produto,  # type:ignore
                    coluna_produto, produto,  # type:ignore
                    coluna_unidade,  # type:ignore
                    coluna_preco_tabela_inclusao,  # type:ignore
                    coluna_preco_venda_medio,  # type:ignore
                    coluna_quantidade,  # type:ignore
                    coluna_cidade, cidade,  # type:ignore
                    coluna_estado, chave_estado,  # type:ignore
                    nao_compraram_depois,  # type:ignore
                    coluna_rentabilidade,  # type:ignore
                    coluna_rentabilidade_valor,  # type:ignore
                )

                valor_mercadorias_total = 0
                mc_total = 0
                mc_valor_total = 0
                for dado in dados:
                    valor_mercadorias_total += dado.get('VALOR_MERCADORIAS')
                    if coluna_rentabilidade or coluna_rentabilidade_valor:
                        mc_valor_total += dado.get('MC_VALOR')
                if mc_valor_total and valor_mercadorias_total:
                    mc_total = mc_valor_total / valor_mercadorias_total * 100

                contexto.update({
                    'dados': dados,
                    'valor_mercadorias_total': valor_mercadorias_total,
                    'mc_total': mc_total,
                    'mc_valor_total': mc_valor_total,
                    'coluna_grupo_economico': coluna_grupo_economico,
                    'coluna_carteira': coluna_carteira,
                    'coluna_tipo_cliente': coluna_tipo_cliente,
                    'coluna_familia_produto': coluna_familia_produto,
                    'coluna_produto': coluna_produto,
                    'coluna_unidade': coluna_unidade,
                    'coluna_preco_tabela_inclusao': coluna_preco_tabela_inclusao,
                    'coluna_preco_venda_medio': coluna_preco_venda_medio,
                    'coluna_quantidade': coluna_quantidade,
                    'coluna_cidade': coluna_cidade,
                    'coluna_estado': coluna_estado,
                    'coluna_rentabilidade': coluna_rentabilidade,
                    'coluna_rentabilidade_valor': coluna_rentabilidade_valor,
                })

            if 'exportar-submit' in request.GET:
                excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)

                response = HttpResponse(
                    arquivo,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="relatorio_faturamento.xlsx"'
                return response

    contexto.update({'formulario': formulario, })

    return render(request, 'dashboards/pages/relatorios-supervisao.html', contexto)
