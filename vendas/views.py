from django.shortcuts import render
from vendas.models import RncNotas
from utils.base_forms import FormPeriodoInicioFimMixIn
from utils.plotly_parametros import update_layout_kwargs
import pandas as pd
import plotly.express as px
import plotly.io as pio


def relatorios_rnc(request):
    """Retorna dados para pagina de relatorios RNC, baseado nos filtros do formulario.

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormPeriodoInicioFimMixIn): com o formulario

    Se o formulario estiver valido:

    :graficos_dados_pie_html (list): com uma lista dos htmls de graficos de pizza
    :graficos_dados_bar_html (list): com uma lista dos htmls de grafico de barras"""
    titulo_pagina = 'Relatorios RNC'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormPeriodoInicioFimMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormPeriodoInicioFimMixIn(request.GET)
        if formulario.is_valid():
            inicio = formulario.cleaned_data.get('inicio')
            fim = formulario.cleaned_data.get('fim')

            # Dados Graficos

            custo_nao_recuperado_por_responsavel = RncNotas.custo_nao_recuperado_por_responsavel(inicio, fim)
            quantidade_por_responsavel = RncNotas.quantidade_por_responsavel(inicio, fim)
            quantidade_por_origem = RncNotas.quantidade_por_origem(inicio, fim)
            quantidade_por_motivo = RncNotas.quantidade_por_motivo(inicio, fim)

            dados_grafico_pie = [
                {
                    'df': pd.DataFrame(quantidade_por_responsavel),
                    'coluna_nome': 'responsavel__nome',
                    'coluna_nome_alias': 'Responsavel',
                    'coluna_valor': 'quantidade',
                    'coluna_valor_alias': 'Quantidade',
                    'coluna_concatenada': 'Responsavel/Qtd',
                    'titulo': 'RNC Por Responsavel',
                },
                {
                    'df': pd.DataFrame(quantidade_por_origem),
                    'coluna_nome': 'origem',
                    'coluna_nome_alias': 'Origem',
                    'coluna_valor': 'quantidade',
                    'coluna_valor_alias': 'Quantidade',
                    'coluna_concatenada': 'Origem/Qtd',
                    'titulo': 'RNC Por Origem',
                },
                {
                    'df': pd.DataFrame(quantidade_por_motivo),
                    'coluna_nome': 'motivo__descricao',
                    'coluna_nome_alias': 'Motivo',
                    'coluna_valor': 'quantidade',
                    'coluna_valor_alias': 'Quantidade',
                    'coluna_concatenada': 'Motivo/Qtd',
                    'titulo': 'RNC Por Motivo',
                },
            ]

            dados_grafico_bar = [
                {
                    'df': pd.DataFrame(custo_nao_recuperado_por_responsavel),
                    'coluna_x': 'responsavel__nome',
                    'coluna_x_alias': 'Responsavel',
                    'coluna_y': 'custo_nao_recuperado',
                    'coluna_y_alias': 'Custo Não Recuperado R$',
                    'titulo': 'Custo Não Recuperado Por Responsavel R$',
                },
            ]

            graficos_dados_pie_html = []
            for dados in dados_grafico_pie:
                df = dados['df']
                coluna_nome = dados['coluna_nome']
                coluna_nome_alias = dados['coluna_nome_alias']
                coluna_valor = dados['coluna_valor']
                coluna_valor_alias = dados['coluna_valor_alias']
                coluna_concatenada = dados['coluna_concatenada']
                titulo = dados['titulo']
                if not df.empty:
                    df.rename(columns={coluna_nome: coluna_nome_alias, coluna_valor: coluna_valor_alias, },
                              inplace=True)
                    df[coluna_concatenada] = df[coluna_nome_alias] + ' - ' + df[coluna_valor_alias].astype(str)

                    # Geração Grafico Pizza
                    grafico = px.pie(df, values=coluna_valor_alias, names=coluna_concatenada, title=titulo,
                                     hover_name=coluna_nome_alias, hover_data={coluna_concatenada: False, })
                    grafico.update_layout(update_layout_kwargs, legend_orientation='v', height=400, width=540,)
                    grafico_html = pio.to_html(grafico, full_html=False)
                    graficos_dados_pie_html.append(grafico_html)

            # Geração Graficos Barra

            graficos_dados_bar_html = []
            for dados in dados_grafico_bar:
                df = dados['df']
                coluna_x = dados['coluna_x']
                coluna_x_alias = dados['coluna_x_alias']
                coluna_y = dados['coluna_y']
                coluna_y_alias = dados['coluna_y_alias']
                titulo = dados['titulo']
                if not df.empty:
                    df.rename(columns={coluna_x: coluna_x_alias, coluna_y: coluna_y_alias, }, inplace=True)

                    # Geração Grafico Barra
                    grafico = px.bar(df, x=coluna_x_alias, y=coluna_y_alias, title=titulo, color=coluna_x_alias,
                                     text_auto=True, hover_name=coluna_x_alias,
                                     hover_data={coluna_x_alias: False, coluna_y_alias: ':,.2f', })
                    grafico.update_layout(update_layout_kwargs)
                    grafico_html = pio.to_html(grafico, full_html=False)
                    graficos_dados_bar_html.append(grafico_html)

            contexto.update({'graficos_dados_pie_html': graficos_dados_pie_html,
                             'graficos_dados_bar_html': graficos_dados_bar_html, })

    contexto.update({'formulario': formulario})

    return render(request, 'vendas/pages/relatorios-rnc.html', contexto)
