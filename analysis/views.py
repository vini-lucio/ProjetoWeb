# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO, STATUS_ORCAMENTOS_ITENS
from dashboards.services import get_relatorios_vendas
import plotly.express as px
import plotly.io as pio
import pandas as pd
from utils.data_hora_atual import data_365_dias_atras, data_x_dias
from utils.plotly_parametros import update_layout_kwargs, update_traces_kwargs, lista_dict_para_dataframe


class GruposEconomicosDetailView(DetailView):
    model = GRUPO_ECONOMICO
    template_name = 'analysis/pages/grupo-economico.html'
    context_object_name = 'grupo_economico'

    def get_queryset(self):
        return super().get_queryset().using('analysis')

    def get_context_data(self, **kwargs):
        # TODO: levar em consideração quando não tiver venda no mes/ano
        # TODO: conferir valores
        context = super().get_context_data(**kwargs)
        objeto = self.get_object()

        titulo_pagina = f'{objeto.DESCRICAO}'  # type: ignore

        # Dados Grupo Economico

        quantidade_clientes = objeto.quantidade_clientes_ativos  # type:ignore
        quantidade_tipos = objeto.quantidade_clientes_ativos_por_tipo  # type:ignore
        quantidade_carteiras = objeto.quantidade_clientes_ativos_por_carteira  # type:ignore
        quantidade_eventos_em_aberto = objeto.quantidade_eventos_em_aberto  # type:ignore
        quantidade_eventos_em_atraso = objeto.quantidade_eventos_em_atraso  # type:ignore
        ultimo_orcamento_aberto = objeto.ultimo_orcamento_aberto  # type:ignore
        ultimo_pedido = objeto.ultimo_pedido  # type:ignore
        media_dias_orcamento_para_pedido = objeto.media_dias_orcamento_para_pedido  # type:ignore

        # Dados Grafico Valor Anual

        historico_faturamento_anual = get_relatorios_vendas(orcamento=False, coluna_ano_emissao=True,
                                                            grupo_economico=objeto.DESCRICAO,)  # type: ignore

        historico_orcamentos_anual = get_relatorios_vendas(orcamento=True, coluna_ano_emissao=True,
                                                           desconsiderar_justificativas=True,
                                                           grupo_economico=objeto.DESCRICAO,)  # type: ignore

        dados_grafico_faturamento = {}
        dados_grafico_orcamentos = {}
        if historico_orcamentos_anual:
            dados_grafico_orcamentos = lista_dict_para_dataframe(historico_orcamentos_anual, 'ANO_EMISSAO',
                                                                 'VALOR_MERCADORIAS', 'Ano Emissão', 'Valor')
            dados_grafico_orcamentos['Fonte'] = 'Orçamentos'
        if historico_faturamento_anual:
            dados_grafico_faturamento = lista_dict_para_dataframe(historico_faturamento_anual, 'ANO_EMISSAO',
                                                                  'VALOR_MERCADORIAS', 'Ano Emissão', 'Valor')
            dados_grafico_faturamento['Fonte'] = 'Faturamento'

        dados_grafico_final = pd.concat([dados_grafico_faturamento,
                                         dados_grafico_orcamentos,], ignore_index=True)  # type: ignore

        grafico_historico = px.line(dados_grafico_final, x='Ano Emissão', y='Valor', title='Historico Anual',
                                    markers=True, text='Valor', color='Fonte',

                                    hover_name='Fonte',
                                    hover_data={
                                        'Fonte': False,
                                        'Ano Emissão': ':,.0f',
                                        'Valor': ':,.2f',
                                    },)
        grafico_historico.update_layout(update_layout_kwargs)
        grafico_historico.update_traces(update_traces_kwargs, textposition='bottom right')
        grafico_historico_html = pio.to_html(grafico_historico, full_html=False)

        # Dados Grafico Produtos

        data_12_meses = data_365_dias_atras()
        produtos_vendidos_12_meses = get_relatorios_vendas(orcamento=False, inicio=data_12_meses, coluna_produto=True,
                                                           grupo_economico=objeto.DESCRICAO,)  # type: ignore
        produtos_vendidos_12_meses = sorted(produtos_vendidos_12_meses, key=lambda x: x['VALOR_MERCADORIAS'],
                                            reverse=True)
        top_30_produtos_vendidos_12_meses = produtos_vendidos_12_meses[:30]

        dados_grafico_produto = {}
        if top_30_produtos_vendidos_12_meses:
            dados_grafico_produto = lista_dict_para_dataframe(top_30_produtos_vendidos_12_meses, 'PRODUTO',
                                                              'VALOR_MERCADORIAS', 'Produto', 'Valor')

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

        # Dados Grafico Status de Orçamentos

        data_2_anos = data_x_dias(730, passado=True)
        quantidade_orcamentos_todos = get_relatorios_vendas(orcamento=True, inicio=data_2_anos, coluna_ano_emissao=True,
                                                            coluna_mes_emissao=True, coluna_quantidade_documentos=True,
                                                            desconsiderar_justificativas=True,
                                                            grupo_economico=objeto.DESCRICAO,)  # type: ignore

        status_fechado = STATUS_ORCAMENTOS_ITENS.objects.using('analysis').get(DESCRICAO='FECHADO')
        quantidade_orcamentos_fechados = get_relatorios_vendas(orcamento=True, inicio=data_2_anos,
                                                               coluna_ano_emissao=True, coluna_mes_emissao=True,
                                                               coluna_quantidade_documentos=True,
                                                               status_produto_orcamento=status_fechado,
                                                               grupo_economico=objeto.DESCRICAO,)  # type: ignore

        dados_grafico_quantidade_orcamentos_todos = {}
        dados_grafico_quantidade_orcamentos_fechado = {}
        if quantidade_orcamentos_todos:
            for ano_mes in quantidade_orcamentos_todos:
                documentos_nao_fechados = ano_mes['QUANTIDADE_DOCUMENTOS']
                for ano_mes_fechado in quantidade_orcamentos_fechados:
                    if ano_mes['ANO_EMISSAO'] == ano_mes_fechado['ANO_EMISSAO'] and ano_mes['MES_EMISSAO'] == ano_mes_fechado['MES_EMISSAO']:
                        documentos_nao_fechados = ano_mes['QUANTIDADE_DOCUMENTOS'] - \
                            ano_mes_fechado['QUANTIDADE_DOCUMENTOS']
                ano_mes.update({'ANO_MES': f'{ano_mes['ANO_EMISSAO']} | {ano_mes['MES_EMISSAO']:02}',
                                'QUANTIDADE_DOCUMENTOS': documentos_nao_fechados})
            dados_grafico_quantidade_orcamentos_todos = lista_dict_para_dataframe(
                quantidade_orcamentos_todos, 'ANO_MES', 'QUANTIDADE_DOCUMENTOS', 'Ano | Mês', 'Documentos'
            )
            dados_grafico_quantidade_orcamentos_todos['Fonte'] = 'Não Fechados'
        if quantidade_orcamentos_fechados:
            for ano_mes in quantidade_orcamentos_fechados:
                ano_mes.update({'ANO_MES': f'{ano_mes['ANO_EMISSAO']} | {ano_mes['MES_EMISSAO']:02}'})
            dados_grafico_quantidade_orcamentos_fechado = lista_dict_para_dataframe(
                quantidade_orcamentos_fechados, 'ANO_MES', 'QUANTIDADE_DOCUMENTOS', 'Ano | Mês', 'Documentos'
            )
            dados_grafico_quantidade_orcamentos_fechado['Fonte'] = 'Fechados'

        dados_grafico_quantidade_orcamentos_final = pd.concat(
            [dados_grafico_quantidade_orcamentos_fechado, dados_grafico_quantidade_orcamentos_todos],  # type: ignore
            ignore_index=True
        ).sort_values(by='Ano | Mês')

        grafico_quantidade_orcamentos = px.bar(dados_grafico_quantidade_orcamentos_final, x='Ano | Mês', y='Documentos',
                                               title='Quantidade de Orçamentos (Ultimos 2 anos)',
                                               text='Documentos', color='Fonte',

                                               hover_name='Fonte',
                                               hover_data={
                                                   'Fonte': False,
                                                   'Ano | Mês': True,
                                                   'Documentos': ':,.0f',
                                               },)
        grafico_quantidade_orcamentos.update_layout(update_layout_kwargs, barmode='stack')
        grafico_quantidade_orcamentos.update_layout(yaxis=dict(tickformat=',.0f'))
        grafico_quantidade_orcamentos_html = pio.to_html(grafico_quantidade_orcamentos, full_html=False)

        # Contexto

        context.update({
            'titulo_pagina': titulo_pagina,
            'quantidade_clientes': quantidade_clientes,
            'quantidade_tipos': quantidade_tipos,
            'quantidade_carteiras': quantidade_carteiras,
            'historico_faturamento_anual': historico_faturamento_anual,
            'quantidade_eventos_em_aberto': quantidade_eventos_em_aberto,
            'quantidade_eventos_em_atraso': quantidade_eventos_em_atraso,
            'grafico_historico_html': grafico_historico_html,
            'top_30_produtos_vendidos_12_meses': top_30_produtos_vendidos_12_meses,
            'grafico_produtos_html': grafico_produtos_html,
            'ultimo_orcamento_aberto': ultimo_orcamento_aberto,
            'ultimo_pedido': ultimo_pedido,
            'grafico_quantidade_orcamentos_html': grafico_quantidade_orcamentos_html,
            'media_dias_orcamento_para_pedido': media_dias_orcamento_para_pedido,
        })
        return context
