# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO
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

        dados_faturamento = get_relatorios_vendas(orcamento=False, coluna_ano_emissao=True, coluna_produto=True,
                                                  coluna_data_emissao=True,
                                                  grupo_economico=objeto.DESCRICAO,)  # type: ignore
        dados_faturamento = pd.DataFrame(dados_faturamento)
        dados_faturamento = dados_faturamento.rename(columns={
            'ANO_EMISSAO': 'Ano Emissão', 'DATA_EMISSAO': 'Data Emissão', 'VALOR_MERCADORIAS': 'Valor',
            'PRODUTO': 'Produto', })

        dados_orcamentos = get_relatorios_vendas(orcamento=True, coluna_ano_mes_emissao=True, coluna_ano_emissao=True,
                                                 coluna_produto=True, coluna_data_emissao=True,
                                                 desconsiderar_justificativas=True, considerar_itens_excluidos=True,
                                                 coluna_status_produto_orcamento=True,
                                                 grupo_economico=objeto.DESCRICAO,)  # type: ignore
        dados_orcamentos = pd.DataFrame(dados_orcamentos)
        dados_orcamentos = dados_orcamentos.rename(columns={
            'ANO_MES_EMISSAO': 'Ano | Mês', 'ANO_EMISSAO': 'Ano Emissão', 'PRODUTO': 'Produto',
            'DATA_EMISSAO': 'Data Emissão', 'STATUS': 'Status', 'VALOR_MERCADORIAS': 'Valor', })  # type:ignore
        dados_orcamentos_nao_fechados = dados_orcamentos[dados_orcamentos['Status'] != 'FECHADO']
        dados_orcamentos_fechados = dados_orcamentos[dados_orcamentos['Status'] == 'FECHADO']

        # Dados Grafico Valor Anual

        grafico_historico_html = ""
        if not dados_faturamento.empty:
            ano_inicio_historico = data_inicio_analysis().year
            ano_fim_historico = hoje().year
            lista_anos_historico = [ano_inicio_historico]
            while ano_inicio_historico != ano_fim_historico:
                ano_inicio_historico += 1
                lista_anos_historico.append(ano_inicio_historico)
            lista_anos_historico = pd.DataFrame({'Ano Emissão': lista_anos_historico, })

            dados_faturamento_historico = dados_faturamento.groupby('Ano Emissão', as_index=False)['Valor'].sum()
            dados_faturamento_historico = dados_faturamento_historico.rename(
                columns={'Valor': 'Faturado', })  # type:ignore

            dados_nao_fechados_historico = dados_orcamentos_nao_fechados.groupby('Ano Emissão', as_index=False)[
                'Valor'].sum()
            dados_nao_fechados_historico = dados_nao_fechados_historico.rename(
                columns={'Valor': 'Não Fechados', })  # type:ignore

            dados_grafico_historico = pd.merge(lista_anos_historico, dados_faturamento_historico,
                                               on='Ano Emissão', how='outer').fillna(0)
            dados_grafico_historico = pd.merge(dados_grafico_historico, dados_nao_fechados_historico,
                                               on='Ano Emissão', how='outer').fillna(0)

            grafico_historico = px.bar(dados_grafico_historico, x='Ano Emissão', y=['Faturado', 'Não Fechados'],
                                       title='Historico Anual', text_auto=True,
                                       labels={'variable': 'Status', 'value': 'Valor'},

                                       hover_name='Ano Emissão',
                                       hover_data={
                                           'Ano Emissão': False,
                                           'variable': True,
                                           'value': ':,.2f', },)
            grafico_historico.update_layout(update_layout_kwargs, barmode='stack')
            grafico_historico.update_xaxes(type='category')
            grafico_historico_html = pio.to_html(grafico_historico, full_html=False)

        # Dados Grafico Produtos
        # TODO: incluir orçamentos não fechados no grafico. Filtro do top 30 ser a soma to total e não fechado

        grafico_produtos_html = ""
        if not dados_faturamento.empty:
            data_12_meses = data_365_dias_atras()

            dados_grafico_produto = dados_faturamento[dados_faturamento['Data Emissão'].dt.date >= data_12_meses]
            dados_grafico_produto = dados_grafico_produto.groupby('Produto', as_index=False)['Valor'].sum()
            dados_grafico_produto = dados_grafico_produto.sort_values(by='Valor',
                                                                      ascending=False).head(30)  # type:ignore

            grafico_produtos = px.bar(dados_grafico_produto, x='Produto', y='Valor',
                                      title='Top 30 Produtos (Ultimos 12 Meses)', text='Valor',

                                      hover_name='Produto',
                                      hover_data={
                                          'Produto': False,
                                          'Valor': ':,.2f',
                                      },)
            grafico_produtos.update_layout(update_layout_kwargs)
            grafico_produtos.update_traces(update_traces_kwargs)
            grafico_produtos_html = pio.to_html(grafico_produtos, full_html=False)

        # Dados Grafico Status de Orçamentos

        grafico_historico_orcamentos_html = ""
        if not dados_orcamentos.empty:
            data_2_anos = data_x_dias(730, passado=True)

            data_inicio_status = data_2_anos + relativedelta(day=1)
            data_fim_status = hoje() + relativedelta(day=1)
            lista_datas_status = [f'{data_inicio_status.year}|{data_inicio_status.month:02}']
            while data_inicio_status != data_fim_status:
                data_inicio_status = data_inicio_status + relativedelta(months=1)
                lista_datas_status.append(
                    f'{data_inicio_status.year}|{data_inicio_status.month:02}')
            lista_datas_status = pd.DataFrame({'Ano | Mês': lista_datas_status, })

            historico_orcamentos_nao_fechados = dados_orcamentos_nao_fechados[
                dados_orcamentos_nao_fechados['Data Emissão'].dt.date >= data_2_anos]
            historico_orcamentos_nao_fechados = historico_orcamentos_nao_fechados.groupby('Ano | Mês', as_index=False)[
                'Valor'].sum()
            historico_orcamentos_nao_fechados = historico_orcamentos_nao_fechados.rename(columns={
                'Valor': 'Não Fechados', })  # type:ignore

            historico_orcamentos_fechados = dados_orcamentos_fechados[
                dados_orcamentos_fechados['Data Emissão'].dt.date >= data_2_anos]
            historico_orcamentos_fechados = historico_orcamentos_fechados.groupby('Ano | Mês', as_index=False)[
                'Valor'].sum()
            historico_orcamentos_fechados = historico_orcamentos_fechados.rename(columns={
                'Valor': 'Fechados', })  # type:ignore

            dados_grafico_historico_orcamentos = pd.merge(lista_datas_status, historico_orcamentos_nao_fechados,
                                                          'outer', 'Ano | Mês').fillna(0)
            dados_grafico_historico_orcamentos = pd.merge(dados_grafico_historico_orcamentos,
                                                          historico_orcamentos_fechados,
                                                          'outer', 'Ano | Mês').fillna(0)

            grafico_historico_orcamentos = px.bar(dados_grafico_historico_orcamentos, x='Ano | Mês',
                                                  y=['Fechados', 'Não Fechados'], text_auto=True,
                                                  title='Historico de Orçamentos Mensais (Ultimos 2 anos)',
                                                  labels={'variable': 'Status', 'value': 'Valor'},

                                                  hover_name='Ano | Mês',
                                                  hover_data={
                                                      'Ano | Mês': False,
                                                      'variable': True,
                                                      'value': ':,.2f',
                                                  },
                                                  )
            grafico_historico_orcamentos.update_layout(update_layout_kwargs, barmode='stack')
            grafico_historico_orcamentos_html = pio.to_html(grafico_historico_orcamentos, full_html=False)

        # Contexto

        context.update({
            'titulo_pagina': titulo_pagina,
            'quantidade_clientes': quantidade_clientes,
            'quantidade_tipos': quantidade_tipos,
            'quantidade_carteiras': quantidade_carteiras,
            'quantidade_eventos_em_aberto': quantidade_eventos_em_aberto,
            'quantidade_eventos_em_atraso': quantidade_eventos_em_atraso,
            'grafico_historico_html': grafico_historico_html,
            'grafico_produtos_html': grafico_produtos_html,
            'ultimo_orcamento_aberto': ultimo_orcamento_aberto,
            'ultimo_pedido': ultimo_pedido,
            'grafico_historico_orcamentos_html': grafico_historico_orcamentos_html,
            'media_dias_orcamento_para_pedido': media_dias_orcamento_para_pedido,
        })
        return context
