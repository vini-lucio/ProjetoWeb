# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO, STATUS_ORCAMENTOS_ITENS
from dashboards.services import get_relatorios_vendas
import plotly.express as px
import plotly.io as pio
import pandas as pd
from utils.data_hora_atual import data_365_dias_atras, data_x_dias, hoje, relativedelta, data_inicio_analysis
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
        quantidade_eventos_em_atraso = objeto.quantidade_eventos_em_atraso  # type:ignore
        ultimo_orcamento_aberto = objeto.ultimo_orcamento_aberto  # type:ignore
        ultimo_pedido = objeto.ultimo_pedido  # type:ignore
        media_dias_orcamento_para_pedido = objeto.media_dias_orcamento_para_pedido  # type:ignore

        # Dados Grafico Valor Anual

        ano_inicio_historico = data_inicio_analysis().year
        ano_fim_historico = hoje().year
        lista_anos_historico = [ano_inicio_historico]
        while ano_inicio_historico != ano_fim_historico:
            ano_inicio_historico += 1
            lista_anos_historico.append(ano_inicio_historico)

        historico_faturamento_anual = get_relatorios_vendas(orcamento=False, coluna_ano_emissao=True,
                                                            grupo_economico=objeto.DESCRICAO,)  # type: ignore

        lista_anos_historico = pd.DataFrame({'Ano Emissão': lista_anos_historico, })
        dados_grafico_faturamento = pd.DataFrame(historico_faturamento_anual)
        dados_grafico_faturamento = dados_grafico_faturamento.rename(columns={'ANO_EMISSAO': 'Ano Emissão',
                                                                              'VALOR_MERCADORIAS': 'Valor'})
        dados_grafico_faturamento = pd.merge(lista_anos_historico, dados_grafico_faturamento,
                                             on='Ano Emissão', how='outer').fillna(0)

        grafico_historico = px.bar(dados_grafico_faturamento, x='Ano Emissão', y='Valor',
                                   title='Historico Anual Faturamento', text='Valor',

                                   hover_name='Ano Emissão',
                                   hover_data={
                                       'Ano Emissão': False,
                                       'Valor': ':,.2f',
                                   },)
        grafico_historico.update_layout(update_layout_kwargs)
        grafico_historico.update_traces(update_traces_kwargs)
        grafico_historico_html = pio.to_html(grafico_historico, full_html=False)

        # Dados Grafico Produtos

        data_12_meses = data_365_dias_atras()
        produtos_vendidos_12_meses = get_relatorios_vendas(orcamento=False, inicio=data_12_meses, coluna_produto=True,
                                                           grupo_economico=objeto.DESCRICAO,)  # type: ignore
        produtos_vendidos_12_meses = sorted(produtos_vendidos_12_meses, key=lambda x: x['VALOR_MERCADORIAS'],
                                            reverse=True)
        top_30_produtos_vendidos_12_meses = produtos_vendidos_12_meses[:30]

        dados_grafico_produto = pd.DataFrame(top_30_produtos_vendidos_12_meses)
        dados_grafico_produto = dados_grafico_produto.rename(columns={'PRODUTO': 'Produto',
                                                                      'VALOR_MERCADORIAS': 'Valor'})

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

        data_inicio_status = data_2_anos + relativedelta(day=1)
        data_fim_status = hoje() + relativedelta(day=1)
        lista_datas_status = [f'{data_inicio_status.year} | {data_inicio_status.month:02}']
        while data_inicio_status != data_fim_status:
            data_inicio_status = data_inicio_status + relativedelta(months=1)
            lista_datas_status.append(
                f'{data_inicio_status.year} | {data_inicio_status.month:02}')

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

        lista_datas_status = pd.DataFrame({'Ano | Mês': lista_datas_status, })

        quantidade_orcamentos_todos = pd.DataFrame(quantidade_orcamentos_todos)
        quantidade_orcamentos_todos['Ano | Mês'] = quantidade_orcamentos_todos['ANO_EMISSAO'].astype(str) + \
            ' | ' + quantidade_orcamentos_todos['MES_EMISSAO'].astype(str).str.zfill(2)
        quantidade_orcamentos_todos = quantidade_orcamentos_todos.drop(
            columns=['ANO_EMISSAO', 'MES_EMISSAO', 'VALOR_MERCADORIAS'])
        quantidade_orcamentos_todos = quantidade_orcamentos_todos.rename(
            columns={'QUANTIDADE_DOCUMENTOS': 'Todos', })

        quantidade_orcamentos_fechados = pd.DataFrame(quantidade_orcamentos_fechados)
        quantidade_orcamentos_fechados['Ano | Mês'] = quantidade_orcamentos_fechados['ANO_EMISSAO'].astype(str) + \
            ' | ' + quantidade_orcamentos_fechados['MES_EMISSAO'].astype(str).str.zfill(2)
        quantidade_orcamentos_fechados = quantidade_orcamentos_fechados.drop(
            columns=['ANO_EMISSAO', 'MES_EMISSAO', 'VALOR_MERCADORIAS'])
        quantidade_orcamentos_fechados = quantidade_orcamentos_fechados.rename(
            columns={'QUANTIDADE_DOCUMENTOS': 'Fechados', })

        dados_grafico_quantidade_orcamentos_final = pd.merge(lista_datas_status, quantidade_orcamentos_todos,
                                                             'outer', 'Ano | Mês').fillna(0)
        dados_grafico_quantidade_orcamentos_final = pd.merge(dados_grafico_quantidade_orcamentos_final,
                                                             quantidade_orcamentos_fechados,
                                                             'outer', 'Ano | Mês').fillna(0)
        dados_grafico_quantidade_orcamentos_final['Não Fechados'] = dados_grafico_quantidade_orcamentos_final['Todos'] - \
            dados_grafico_quantidade_orcamentos_final['Fechados']

        grafico_quantidade_orcamentos = px.bar(dados_grafico_quantidade_orcamentos_final, x='Ano | Mês',
                                               y=['Fechados', 'Não Fechados'],
                                               title='Quantidade de Orçamentos (Ultimos 2 anos)', text_auto=True,

                                               hover_name='Ano | Mês',
                                               hover_data={
                                                   'Ano | Mês': False,
                                                   'variable': True,
                                                   'value': ':,.0f',
                                               },
                                               )
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
