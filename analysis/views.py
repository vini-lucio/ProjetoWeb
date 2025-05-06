# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO
from dashboards.services import get_relatorios_vendas
import plotly.express as px
import plotly.io as pio
import pandas as pd
import numpy as np
from utils.data_hora_atual import data_365_dias_atras, data_x_dias, hoje
from utils.plotly_parametros import update_layout_kwargs
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


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

        dados_faturamento = get_relatorios_vendas(fonte='faturamentos', coluna_ano_emissao=True, coluna_produto=True,
                                                  coluna_data_emissao=True,
                                                  grupo_economico=objeto.DESCRICAO,)  # type: ignore
        dados_faturamento = pd.DataFrame(dados_faturamento)
        dados_faturamento = dados_faturamento.rename(columns={
            'ANO_EMISSAO': 'Ano Emissão', 'DATA_EMISSAO': 'Data Emissão', 'VALOR_MERCADORIAS': 'Valor',
            'PRODUTO': 'Produto', })

        dados_orcamentos = get_relatorios_vendas(fonte='orcamentos', coluna_ano_mes_emissao=True, coluna_ano_emissao=True,
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
            data_5_anos = data_x_dias(1825, passado=True, sempre_dia_1=True, sempre_mes_1=True)

            ano_inicio_historico = data_5_anos.year
            ano_fim_historico = hoje().year
            lista_anos_historico = range(ano_inicio_historico, ano_fim_historico + 1)
            lista_anos_historico = pd.DataFrame({'Ano Emissão': lista_anos_historico, })

            dados_faturamento_historico = dados_faturamento[dados_faturamento['Data Emissão'].dt.date >= data_5_anos]
            dados_faturamento_historico = dados_faturamento_historico.groupby(
                'Ano Emissão', as_index=False)['Valor'].sum()
            dados_faturamento_historico = dados_faturamento_historico.rename(
                columns={'Valor': 'Faturado', })  # type:ignore

            dados_nao_fechados_historico = dados_orcamentos_nao_fechados[
                dados_orcamentos_nao_fechados['Data Emissão'].dt.date >= data_5_anos]
            dados_nao_fechados_historico = dados_nao_fechados_historico.groupby('Ano Emissão', as_index=False)[
                'Valor'].sum()
            dados_nao_fechados_historico = dados_nao_fechados_historico.rename(
                columns={'Valor': 'Não Fechados', })  # type:ignore

            dados_grafico_historico = pd.merge(lista_anos_historico, dados_faturamento_historico,
                                               on='Ano Emissão', how='outer').fillna(0)
            dados_grafico_historico = pd.merge(dados_grafico_historico, dados_nao_fechados_historico,
                                               on='Ano Emissão', how='outer').fillna(0)

            grafico_historico = px.bar(dados_grafico_historico, x='Ano Emissão', y=['Faturado', 'Não Fechados'],
                                       title='Historico Anual (Ultimos 5 Anos)', text_auto=True,
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

        grafico_produtos_html = ""
        if not dados_faturamento.empty:
            data_12_meses = data_365_dias_atras()

            dados_faturamento_produto = dados_faturamento[dados_faturamento['Data Emissão'].dt.date >= data_12_meses]
            dados_faturamento_produto = dados_faturamento_produto.groupby('Produto', as_index=False)['Valor'].sum()
            dados_faturamento_produto = dados_faturamento_produto.rename(
                columns={'Valor': 'Faturado', })  # type:ignore

            dados_nao_fechados_produto = dados_orcamentos_nao_fechados[
                dados_orcamentos_nao_fechados['Data Emissão'].dt.date >= data_12_meses]
            dados_nao_fechados_produto = dados_nao_fechados_produto.groupby('Produto', as_index=False)['Valor'].sum()
            dados_nao_fechados_produto = dados_nao_fechados_produto.rename(
                columns={'Valor': 'Não Fechados', })  # type:ignore

            dados_grafico_produto = pd.merge(dados_faturamento_produto, dados_nao_fechados_produto,
                                             on='Produto', how='outer').fillna(0)
            dados_grafico_produto['Valor Total'] = dados_grafico_produto['Faturado'] + \
                dados_grafico_produto['Não Fechados']
            dados_grafico_produto = dados_grafico_produto.sort_values(by='Valor Total',
                                                                      ascending=False).head(30)  # type:ignore

            grafico_produtos = px.bar(dados_grafico_produto, x='Produto', y=['Faturado', 'Não Fechados'],
                                      title='Top 30 Produtos (Ultimos 12 Meses)', text_auto=True,
                                      labels={'variable': 'Status', 'value': 'Valor'},

                                      hover_name='Produto',
                                      hover_data={
                                          'Produto': False,
                                          'variable': True,
                                          'value': ':,.2f', },)
            grafico_produtos.update_layout(update_layout_kwargs, barmode='stack')
            grafico_produtos_html = pio.to_html(grafico_produtos, full_html=False)

        # Dados Grafico Status de Orçamentos

        previsao = {}
        grafico_historico_orcamentos_html = ""
        if not dados_orcamentos.empty:
            data_2_anos = data_x_dias(730, passado=True, sempre_dia_1=True)

            lista_datas_status = pd.date_range(data_2_anos, periods=25, freq='ME')
            lista_datas_status = pd.DataFrame({'Ano | Mês': lista_datas_status, })
            lista_datas_status['Ano | Mês'] = lista_datas_status['Ano | Mês'].dt.strftime('%Y-%m')

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

            # Regressão polinomial e media movel

            dados_grafico_historico_orcamentos['Mês Indice'] = range(1, len(dados_grafico_historico_orcamentos) + 1)

            historico_orcamentos_tratado = dados_grafico_historico_orcamentos.drop(
                dados_grafico_historico_orcamentos.index[-1])

            x = historico_orcamentos_tratado[['Mês Indice']]
            y = historico_orcamentos_tratado['Fechados']

            poly = PolynomialFeatures(degree=3, include_bias=False)
            poly_features = poly.fit_transform(x)
            poly_reg_model = LinearRegression()
            poly_reg_model.fit(poly_features, y)
            y_predicted = poly_reg_model.predict(poly_features)
            historico_orcamentos_tratado['Poly'] = y_predicted
            poly_r_squared = poly_reg_model.score(poly_features, y)
            poly_rmse = np.sqrt(mean_squared_error(y, y_predicted))

            mes_seguinte_poly = pd.DataFrame({'Mês Indice': [len(historico_orcamentos_tratado) + 1]})
            mes_seguinte_poly = mes_seguinte_poly[['Mês Indice']]
            mes_seguinte_poly = poly.fit_transform(mes_seguinte_poly)
            mes_seguinte_poly = poly_reg_model.predict(mes_seguinte_poly)

            historico_orcamentos_tratado['Media Movel'] = historico_orcamentos_tratado['Fechados'].rolling(
                window=3
            ).mean()
            historico_orcamentos_tratado = historico_orcamentos_tratado.dropna(subset=['Media Movel'])
            media_movel_rmse = np.sqrt(mean_squared_error(historico_orcamentos_tratado['Fechados'],
                                                          historico_orcamentos_tratado['Media Movel']))
            media_movel_r_squared = r2_score(historico_orcamentos_tratado['Fechados'],
                                             historico_orcamentos_tratado['Media Movel'])
            mes_seguinte_media_movel = historico_orcamentos_tratado['Media Movel'].iloc[-1]

            if poly_r_squared >= media_movel_r_squared:
                previsao['metodo'] = 'Regressão Polinomial'
                previsao['mes_seguinte'] = float(mes_seguinte_poly[0])
                previsao['r_squared'] = poly_r_squared * 100
                previsao['rmse'] = float(poly_rmse)
            else:
                previsao['metodo'] = 'Media Movel'
                previsao['mes_seguinte'] = float(mes_seguinte_media_movel)
                previsao['r_squared'] = media_movel_r_squared * 100
                previsao['rmse'] = float(media_movel_rmse)

            dados_grafico_historico_orcamentos['Previsão Fechamento'] = 0
            linha_previsao = {'Ano | Mês': 'Previsão Mês Atual', 'Previsão Fechamento': previsao['mes_seguinte'], }
            dados_grafico_historico_orcamentos.loc[len(
                dados_grafico_historico_orcamentos)] = linha_previsao  # type:ignore

            grafico_historico_orcamentos = px.bar(dados_grafico_historico_orcamentos, x='Ano | Mês',
                                                  y=['Fechados', 'Não Fechados', 'Previsão Fechamento'], text_auto=True,
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
            grafico_historico_orcamentos.update_xaxes(type='category')
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
            'previsao': previsao,
        })
        return context
