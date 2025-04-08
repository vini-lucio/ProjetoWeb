# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO
from dashboards.services import get_relatorios_vendas
import plotly.express as px
import plotly.io as pio
import pandas as pd
from utils.data_hora_atual import data_365_dias_atras
from utils.plotly_parametros import update_layout_kwargs, update_traces_kwargs


class GruposEconomicosDetailView(DetailView):
    model = GRUPO_ECONOMICO
    template_name = 'analysis/pages/grupo-economico.html'
    context_object_name = 'grupo_economico'

    def get_queryset(self):
        return super().get_queryset().using('analysis')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        objeto = self.get_object()

        titulo_pagina = f'{objeto.DESCRICAO}'  # type: ignore

        # Dados Grupo Economico

        quantidade_clientes = objeto.quantidade_clientes_ativos  # type:ignore
        quantidade_tipos = objeto.quantidade_clientes_ativos_por_tipo  # type:ignore
        quantidade_carteiras = objeto.quantidade_clientes_ativos_por_carteira  # type:ignore
        quantidade_eventos_em_aberto = objeto.quantidade_eventos_em_aberto  # type:ignore

        # Dados Grafico Valor Anual

        historico_faturamento_anual = get_relatorios_vendas(
            orcamento=False,
            grupo_economico=objeto.DESCRICAO,  # type: ignore
            coluna_ano_emissao=True,
        )

        historico_orcamentos_anual = get_relatorios_vendas(
            orcamento=True,
            grupo_economico=objeto.DESCRICAO,  # type: ignore
            coluna_ano_emissao=True,
        )

        dados_grafico_faturamento = {}
        dados_grafico_orcamentos = {}
        if historico_orcamentos_anual:
            anos_orcamentos = [ano['ANO_EMISSAO'] for ano in historico_orcamentos_anual]
            valores_orcamentos = [round(ano['VALOR_MERCADORIAS'], 2) for ano in historico_orcamentos_anual]
            dados_grafico_orcamentos.update({'Ano Emissão': anos_orcamentos, 'Valor': valores_orcamentos})
            dados_grafico_orcamentos = pd.DataFrame(dados_grafico_orcamentos)
            dados_grafico_orcamentos['Fonte'] = 'Orçamentos'
        if historico_faturamento_anual:
            anos_faturamento = [ano['ANO_EMISSAO'] for ano in historico_faturamento_anual]
            valores_faturamento = [round(ano['VALOR_MERCADORIAS'], 2) for ano in historico_faturamento_anual]
            dados_grafico_faturamento.update({'Ano Emissão': anos_faturamento, 'Valor': valores_faturamento})
            dados_grafico_faturamento = pd.DataFrame(dados_grafico_faturamento)
            dados_grafico_faturamento['Fonte'] = 'Faturamento'

        dados_grafico_final = pd.concat([dados_grafico_faturamento,
                                         dados_grafico_orcamentos,], ignore_index=True)  # type: ignore

        grafico_historico = px.line(dados_grafico_final, x='Ano Emissão', y='Valor',
                                    title='Historico Anual',
                                    markers=True, text='Valor', color='Fonte',

                                    hover_name='Fonte',
                                    hover_data={
                                        'Fonte': False,
                                        'Ano Emissão': ':,.0f',
                                        'Valor': ':,.2f',
                                    },)
        grafico_historico.update_layout(update_layout_kwargs)
        grafico_historico.update_traces(update_traces_kwargs, textposition='bottom right',)
        grafico_historico_html = pio.to_html(grafico_historico, full_html=False)

        # Dados Grafico Produtos

        data_12_meses = data_365_dias_atras()
        produtos_vendidos_12_meses = get_relatorios_vendas(
            inicio=data_12_meses,
            orcamento=False,
            grupo_economico=objeto.DESCRICAO,  # type: ignore
            coluna_produto=True,
        )
        produtos_vendidos_12_meses = sorted(produtos_vendidos_12_meses, key=lambda x: x['VALOR_MERCADORIAS'],
                                            reverse=True)
        top_30_produtos_vendidos_12_meses = produtos_vendidos_12_meses[:30]

        dados_grafico_produto = {}
        if top_30_produtos_vendidos_12_meses:
            produto = [produto['PRODUTO'] for produto in top_30_produtos_vendidos_12_meses]
            valores_produto = [round(produto['VALOR_MERCADORIAS'], 2) for produto in top_30_produtos_vendidos_12_meses]
            dados_grafico_produto.update({'Produto': produto, 'Valor': valores_produto})
            dados_grafico_produto = pd.DataFrame(dados_grafico_produto)
            dados_grafico_produto['Fonte'] = 'Faturamento'

        grafico_produtos = px.bar(dados_grafico_produto, x='Produto', y='Valor',
                                  title='Historico Produtos (Top 30) Ultimos 12 Meses', text='Valor',

                                  hover_name='Produto',
                                  hover_data={
                                      'Produto': False,
                                      'Valor': ':,.2f',
                                  },)
        grafico_produtos.update_layout(update_layout_kwargs)
        grafico_produtos.update_traces(update_traces_kwargs)
        grafico_produtos_html = pio.to_html(grafico_produtos, full_html=False)

        # Contexto

        context.update({
            'titulo_pagina': titulo_pagina,
            'quantidade_clientes': quantidade_clientes,
            'quantidade_tipos': quantidade_tipos,
            'quantidade_carteiras': quantidade_carteiras,
            'historico_faturamento_anual': historico_faturamento_anual,
            'quantidade_eventos_em_aberto': quantidade_eventos_em_aberto,
            'grafico_historico_html': grafico_historico_html,
            'top_30_produtos_vendidos_12_meses': top_30_produtos_vendidos_12_meses,
            'grafico_produtos_html': grafico_produtos_html,
        })
        return context
