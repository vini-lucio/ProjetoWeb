# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO
from dashboards.services import get_relatorios_vendas
import plotly.express as px
import plotly.io as pio


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

        quantidade_clientes = objeto.quantidade_clientes_ativos  # type:ignore
        quantidade_tipos = objeto.quantidade_clientes_ativos_por_tipo  # type:ignore
        quantidade_carteiras = objeto.quantidade_clientes_ativos_por_carteira  # type:ignore
        quantidade_eventos_em_aberto = objeto.quantidade_eventos_em_aberto  # type:ignore

        historico_faturamento_anual = get_relatorios_vendas(
            orcamento=False,
            grupo_economico=objeto.DESCRICAO,  # type: ignore
            coluna_ano_emissao=True,
            coluna_quantidade_documentos=True,
        )

        # print(px.data.gapminder().query("country in ['Canada', 'Botswana']"))

        dados_grafico = {}
        if historico_faturamento_anual:
            anos = [ano['ANO_EMISSAO'] for ano in historico_faturamento_anual]
            valores = [round(ano['VALOR_MERCADORIAS'], 2) for ano in historico_faturamento_anual]
            dados_grafico.update({'Ano Emissão': anos, 'Valor': valores})

        grafico_historico = px.line(dados_grafico, x='Ano Emissão', y='Valor', title='Historico Anual de Faturamento',
                                    markers=True, text='Valor',)
        grafico_historico.update_layout(
            title=dict(font_size=30, font_color='rgb(189, 198, 56)', x=0.5,),
            font=dict(color='rgb(0, 50, 105)', family='Arial',),
            margin=dict(b=10, l=10, r=10, t=60,),
            height=600,
            separators=',.',
            paper_bgcolor='rgb(0, 0, 0, 0)',
            plot_bgcolor='rgb(0, 0, 0, 0)',

            yaxis=dict(tickformat=',.2f', gridcolor='rgba(189, 198, 56, 0.5)', zerolinecolor="rgba(0, 50, 105, 0.2)",),
            xaxis=dict(tickformat=',.0f', gridcolor='rgba(189, 198, 56, 0.5)',),
        )
        grafico_historico.update_traces(
            hoverinfo='x+y',
            texttemplate='%{text:.2s}',
            textposition='bottom right',
        )

        grafico_historico_html = pio.to_html(grafico_historico, full_html=False)

        context.update({
            'titulo_pagina': titulo_pagina,
            'quantidade_clientes': quantidade_clientes,
            'quantidade_tipos': quantidade_tipos,
            'quantidade_carteiras': quantidade_carteiras,
            'historico_faturamento_anual': historico_faturamento_anual,
            'quantidade_eventos_em_aberto': quantidade_eventos_em_aberto,
            'grafico_historico_html': grafico_historico_html,
        })
        return context
