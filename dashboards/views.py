from typing import Dict, Literal
from django.shortcuts import render
from django.http import HttpResponse
from .models import IndicadoresValores, MetasCarteiras
from .services import (DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_vendas, get_email_contatos,
                       DashboardVendasCarteira, eventos_dia_atrasos, confere_orcamento, eventos_em_aberto_por_dia,
                       confere_inscricoes_estaduais)
from .forms import (RelatoriosSupervisaoFaturamentosForm, RelatoriosSupervisaoOrcamentosForm,
                    FormDashboardVendasCarteiras, FormAnaliseOrcamentos, FormEventos, FormEventosDesconsiderar,
                    FormIndicadores)
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario, arquivo_excel_response
from utils.data_hora_atual import data_x_dias
from utils.base_forms import FormVendedoresMixIn
from utils.cor_rentabilidade import get_cores_rentabilidade
from utils.plotly_parametros import update_layout_kwargs
from utils.site_setup import get_site_setup
import pandas as pd
import numpy as np


def vendas_carteira(request):
    titulo_pagina = 'Dashboard Vendas'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormDashboardVendasCarteiras()

    if request.method == 'GET' and request.GET:
        formulario = FormDashboardVendasCarteiras(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Total'

            carteira_parametros = {'carteira': carteira}
            if carteira_nome == 'PAREDE DE CONCRETO':
                carteira_parametros = {'carteira_parede_de_concreto': True}
            if carteira_nome == 'PREMOLDADO / POSTE':
                carteira_parametros = {'carteira_premoldado_poste': True}

            if 'atualizar-submit' in request.GET:
                dados = DashboardVendasCarteira(carteira=carteira_nome)

                fonte: Literal['orcamentos', 'pedidos',
                               'faturamentos'] = formulario.cleaned_data.get('fonte')  # type: ignore
                em_aberto: bool = formulario.cleaned_data.get(
                    'em_aberto') if fonte != 'faturamentos' else False  # type: ignore
                inicio = formulario.cleaned_data.get('inicio') if not em_aberto else None
                fim = formulario.cleaned_data.get('fim') if not em_aberto else None

                valores_periodo = get_relatorios_vendas(fonte=fonte, inicio=inicio, fim=fim, coluna_data_emissao=True,
                                                        coluna_status_documento=True, coluna_job=True,
                                                        status_documento_em_aberto=em_aberto,
                                                        coluna_rentabilidade=True, coluna_documento=True,
                                                        coluna_rentabilidade_cor=True, coluna_cliente=True,
                                                        coluna_grupo_economico=True, coluna_data_entrega_itens=True,
                                                        coluna_orcamento_oportunidade=True,
                                                        incluir_orcamentos_oportunidade=True, coluna_carteira=True,
                                                        **carteira_parametros)

                valor_total = 0
                valor_liquidados = 0
                valor_em_abertos = 0
                valor_perdidos = 0
                valor_oportunidades_em_aberto = 0
                valor_devolucoes = 0
                for valor in valores_periodo:
                    valor_total += valor.get('VALOR_MERCADORIAS')  # type:ignore

                    if fonte in ('orcamentos', 'pedidos'):
                        if valor.get('STATUS_DOCUMENTO') == 'LIQUIDADO':
                            valor_liquidados += valor.get('VALOR_MERCADORIAS')  # type:ignore

                    if fonte == 'pedidos':
                        if valor.get('STATUS_DOCUMENTO') in ('EM ABERTO', 'BLOQUEADO'):
                            valor_em_abertos += valor.get('VALOR_MERCADORIAS')  # type:ignore

                    if fonte == 'orcamentos':
                        if valor.get('STATUS_DOCUMENTO') == 'PERDIDO':
                            valor_perdidos += valor.get('VALOR_MERCADORIAS')  # type:ignore
                        if valor.get('OPORTUNIDADE') == 'SIM' and valor.get('STATUS_DOCUMENTO') in ('EM ABERTO', 'BLOQUEADO'):
                            valor_oportunidades_em_aberto += valor.get('VALOR_MERCADORIAS')  # type:ignore
                        if valor.get('OPORTUNIDADE') == 'NAO' and valor.get('STATUS_DOCUMENTO') in ('EM ABERTO', 'BLOQUEADO'):
                            valor_em_abertos += valor.get('VALOR_MERCADORIAS')  # type:ignore

                    if fonte == 'faturamentos':
                        if valor.get('VALOR_MERCADORIAS') < 0:  # type:ignore
                            valor_devolucoes += valor.get('VALOR_MERCADORIAS')  # type:ignore

                contexto.update({'dados': dados,
                                'valores_periodo': valores_periodo,
                                 'valor_total': valor_total,
                                 'valor_liquidados': valor_liquidados,
                                 'valor_em_abertos': valor_em_abertos,
                                 'valor_perdidos': valor_perdidos,
                                 'valor_oportunidades_em_aberto': valor_oportunidades_em_aberto,
                                 'valor_devolucoes': valor_devolucoes})

            if 'exportar-orcamentos-submit' in request.GET:
                orcamentos_em_aberto = get_relatorios_vendas(fonte='orcamentos', coluna_job=True, coluna_carteira=True,
                                                             coluna_data_emissao=True,
                                                             coluna_peso_produto_proprio=True,
                                                             status_documento_em_aberto=True, coluna_documento=True,
                                                             coluna_cliente=True, coluna_data_entrega_itens=True,
                                                             coluna_orcamento_oportunidade=True,
                                                             coluna_log_nome_inclusao_documento=True,
                                                             coluna_proximo_evento_grupo_economico=True,
                                                             incluir_orcamentos_oportunidade=True,
                                                             **carteira_parametros)
                excel = arquivo_excel(orcamentos_em_aberto, cabecalho_negrito=True, formatar_numero=(['J', 'K'], 2),
                                      formatar_data=['B', 'C', 'I'], ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'ORCAMENTOS_EM_ABERTO'
                nome_arquivo += f'_{carteira_nome}' if carteira_nome != '%%' else '_TODOS'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/vendas-carteira.html', contexto)


def analise_orcamentos(request):
    titulo_pagina = 'Analise Orçamento'

    cores_rentabilidade = get_cores_rentabilidade()
    cores_rentabilidade.update({'verde': cores_rentabilidade['verde'] + cores_rentabilidade['despesa_adm']})
    cores_rentabilidade.update({'amarelo': cores_rentabilidade['amarelo'] + cores_rentabilidade['despesa_adm']})
    cores_rentabilidade.update({'vermelho': cores_rentabilidade['vermelho'] + cores_rentabilidade['despesa_adm']})

    contexto: dict = {'titulo_pagina': titulo_pagina, 'cores_rentabilidade': cores_rentabilidade, }

    formulario = FormAnaliseOrcamentos(usuario=request.user)

    if request.method == 'GET' and request.GET:
        formulario = FormAnaliseOrcamentos(request.GET, usuario=request.user)
        if formulario.is_valid():
            orcamento = formulario.cleaned_data.get('pesquisar')
            contexto['titulo_pagina'] += f' {orcamento}'

            dados = get_relatorios_vendas(fonte='orcamentos', documento=orcamento, coluna_produto=True,
                                          incluir_orcamentos_oportunidade=True, coluna_preco_venda=True,
                                          coluna_desconto=True, coluna_rentabilidade=True, coluna_quantidade=True,
                                          coluna_frete_incluso_item=True, coluna_custo_total_item=True,
                                          coluna_aliquotas_itens=True, coluna_preco_tabela_inclusao=True,
                                          ordenar_sequencia_prioritario=True, coluna_rentabilidade_cor=True,
                                          coluna_mc_cor_ajuste=True, nao_converter_moeda=True,)
            if dados:
                dt_dados = pd.DataFrame(dados)

                tipo_desconto = formulario.cleaned_data.get('desconto')
                valor = float(formulario.cleaned_data.get('valor'))  # type:ignore

                dt_dados['TIPO_DESCONTO'] = tipo_desconto
                dt_dados['VALOR'] = 1 - (valor / 100)
                dt_dados['FRETE_INCLUSO_ITEM_UNITARIO'] = dt_dados['FRETE_INCLUSO_ITEM'] / dt_dados['QUANTIDADE']
                dt_dados['CUSTO_UNITARIO_ITEM'] = dt_dados['CUSTO_TOTAL_ITEM'] / dt_dados['QUANTIDADE']

                if tipo_desconto == 'desconto_preco_tabela':
                    dt_dados['PRECO_NOVO'] = dt_dados['PRECO_TABELA_INCLUSAO'] * dt_dados['VALOR']
                if tipo_desconto == 'desconto_preco_atual':
                    dt_dados['PRECO_NOVO'] = dt_dados['PRECO_VENDA'] * dt_dados['VALOR']

                if tipo_desconto == 'desconto_preco_tabela' or tipo_desconto == 'desconto_preco_atual':
                    dt_dados['DESCONTO_NOVO'] = (1 - dt_dados['PRECO_NOVO'] / dt_dados['PRECO_TABELA_INCLUSAO']) * 100
                    dt_dados['PRECO_NOVO_SEM_FRETE'] = dt_dados['PRECO_NOVO'] - dt_dados['FRETE_INCLUSO_ITEM_UNITARIO']
                    dt_dados['CUSTO_VARIAVEL_NOVO'] = dt_dados['ALIQUOTAS_TOTAIS'] / \
                        100 * dt_dados['PRECO_NOVO_SEM_FRETE']
                    dt_dados['MC_VALOR_NOVO'] = (
                        dt_dados['PRECO_NOVO_SEM_FRETE'] -
                        dt_dados['CUSTO_UNITARIO_ITEM'] - dt_dados['CUSTO_VARIAVEL_NOVO']
                    )
                    dt_dados['MC_NOVO'] = dt_dados['MC_VALOR_NOVO'] / dt_dados['PRECO_NOVO_SEM_FRETE'] * 100
                    dt_dados['MC_COR_NOVO'] = dt_dados['MC_NOVO'] + dt_dados['MC_COR_AJUSTE']

                if tipo_desconto == 'margem':
                    dt_dados['MC_COR_NOVO'] = valor
                    dt_dados['MC_NOVO'] = dt_dados['MC_COR_NOVO'] - dt_dados['MC_COR_AJUSTE']
                    dt_dados['MARKUP_DIVISOR'] = 1 - (dt_dados['ALIQUOTAS_TOTAIS'] + dt_dados['MC_NOVO']) / 100
                    dt_dados['PRECO_NOVO'] = (
                        dt_dados['CUSTO_UNITARIO_ITEM'] / dt_dados['MARKUP_DIVISOR'] +
                        dt_dados['FRETE_INCLUSO_ITEM_UNITARIO']
                    )
                    dt_dados['DESCONTO_NOVO'] = (1 - dt_dados['PRECO_NOVO'] / dt_dados['PRECO_TABELA_INCLUSAO']) * 100

                dados = dt_dados.to_dict(orient='records')

                confere = confere_orcamento(orcamento)  # type:ignore
                confere_ie = confere_inscricoes_estaduais('orcamentos', {'documento': orcamento})  # type:ignore
                contexto.update({'dados': dados, 'confere_orcamento': confere,
                                 'confere_inscricoes_estaduais': confere_ie})

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/analise_orcamentos.html', contexto)


def detalhes_dia(request):
    titulo_pagina = 'Detalhes'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormVendedoresMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormVendedoresMixIn(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            carteira_parametros = carteira.carteira_parametros()  # type:ignore

            site_setup = get_site_setup()
            inicio = None
            fim = None
            if site_setup:
                inicio = site_setup.primeiro_dia_mes
                fim = site_setup.ultimo_dia_mes
            dados = get_relatorios_vendas(fonte='pedidos', inicio=inicio, fim=fim, coluna_familia_produto=True,
                                          **carteira_parametros)

            contexto.update({'dados': dados, })

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/detalhes-dia.html', contexto)


def eventos_dia(request):
    titulo_pagina = 'Eventos do Dia'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormEventos()

    if request.method == 'GET' and request.GET:
        formulario = FormEventos(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            incluir_futuros = formulario.cleaned_data.get('incluir_futuros', False)
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            dados = eventos_dia_atrasos(carteira=carteira_nome, incluir_futuros=incluir_futuros)

            contexto.update({'dados': dados, })

            if 'exportar-submit' in request.GET:
                if dados:
                    excel = arquivo_excel(dados, cabecalho_negrito=True, formatar_numero=(['G'], 2),
                                          formatar_data=['D'], ajustar_largura_colunas=True)
                    arquivo = salvar_excel_temporario(excel)
                    nome_arquivo = 'EVENTOS'
                    nome_arquivo += f'_{carteira_nome}' if carteira_nome != '%%' else '_TODOS'
                    response = arquivo_excel_response(arquivo, nome_arquivo)
                    return response

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/eventos-dia.html', contexto)


def eventos_por_dia(request):
    titulo_pagina = 'Eventos Por Dia'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormVendedoresMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormVendedoresMixIn(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            dados = eventos_em_aberto_por_dia(carteira=carteira_nome)

            contexto.update({'dados': dados, })

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/eventos-por-dia.html', contexto)


# TODO: usuario poder mudar parametro para aumentar lista?
def listagens(request, listagem: str):
    if listagem not in ('sumidos', 'nuncamais', 'presentes', 'potenciais',):
        return HttpResponse("Pagina invalida", status=404)

    titulo_pagina = f'Os {listagem}'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormEventosDesconsiderar()

    if request.method == 'GET' and request.GET:
        formulario = FormEventosDesconsiderar(request.GET)
        if formulario.is_valid():
            desconsiderar_futuros = formulario.cleaned_data.get('desconsiderar_futuros')
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            carteira_parametros = {'carteira': carteira}
            if carteira_nome == 'PAREDE DE CONCRETO':
                carteira_parametros = {'carteira_parede_de_concreto': True}
            if carteira_nome == 'PREMOLDADO / POSTE':
                carteira_parametros = {'carteira_premoldado_poste': True}

            parametros_comuns = {'coluna_media_dia': True, 'coluna_grupo_economico': True, 'coluna_carteira': True,
                                 'coluna_tipo_cliente': True, 'coluna_quantidade_meses': True,
                                 'status_cliente_ativo': True, 'ordenar_valor_descrescente_prioritario': True,
                                 'nao_compraram_depois': True, 'desconsiderar_justificativas': True,
                                 'considerar_itens_excluidos': True, }
            if desconsiderar_futuros:
                parametros_comuns.update({'desconsiderar_grupo_economico_com_evento_futuro': True})

            descricao_listagem = ''
            if listagem == 'sumidos':
                descricao_listagem = 'Grupos que compravam com frequencia (em 1 ano) e não compram a 6 meses'
                inicio = data_x_dias(180 + 365, passado=True)
                fim = data_x_dias(180, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=2,  # originalmente 3
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'presentes':
                descricao_listagem = 'Grupos que compram quase todo mês (em 6 meses) e não compram a 2 meses'
                inicio = data_x_dias(60 + 180, passado=True)
                fim = data_x_dias(60, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=2,  # originalmente 3
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'nuncamais':
                descricao_listagem = 'Grupos que compravam com frequencia (desde sempre) e não compram a 2 anos'
                inicio = None
                fim = data_x_dias(730, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=7,  # originalmente 9
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'potenciais':
                descricao_listagem = 'Grupos que perdem mais que compram nos ultimos 2 anos'
                inicio = data_x_dias(1 + 730, passado=True)
                fim = data_x_dias(1, passado=True)

                fechados = get_relatorios_vendas(fonte='orcamentos', inicio=inicio, fim=fim,
                                                 status_produto_orcamento_tipo='FECHADO',
                                                 **parametros_comuns, **carteira_parametros)
                perdidos = get_relatorios_vendas(fonte='orcamentos', inicio=inicio, fim=fim,
                                                 status_produto_orcamento_tipo='PERDIDO_CANCELADO',
                                                 **parametros_comuns, **carteira_parametros)

                dt_fechados = pd.DataFrame(fechados)
                dt_fechados.drop(columns=['QUANTIDADE_MESES', 'MEDIA_DIA'], inplace=True)
                dt_fechados.rename(columns={'VALOR_MERCADORIAS': 'VALOR_FECHADOS'}, inplace=True)

                dt_perdidos = pd.DataFrame(perdidos)

                dt_dados = pd.merge(dt_fechados, dt_perdidos, how='outer', on=['CHAVE_GRUPO_ECONOMICO', 'GRUPO',
                                                                               'CARTEIRA', 'TIPO_CLIENTE']).fillna(0)
                dt_dados = dt_dados.loc[dt_dados['VALOR_MERCADORIAS'] > dt_dados['VALOR_FECHADOS']]
                dt_dados = dt_dados.loc[dt_dados['VALOR_MERCADORIAS'] >= 10000]
                dt_dados = dt_dados.sort_values('VALOR_MERCADORIAS', ascending=False)

                dados = dt_dados.to_dict(orient='records')

            contexto.update({'dados': dados, 'descricao_listagem': descricao_listagem})

            if 'exportar-submit' in request.GET:
                if dados:
                    excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True,
                                          formatar_numero=(['F', 'G'], 2))
                    arquivo = salvar_excel_temporario(excel)
                    nome_arquivo = listagem.upper()
                    nome_arquivo += f'_{carteira_nome}' if carteira_nome != '%%' else '_TODOS'
                    response = arquivo_excel_response(arquivo, nome_arquivo)
                    return response

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/listagens.html', contexto)


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    dados = DashboardVendasTv()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)


def vendas_supervisao(request):
    titulo_pagina = 'Dashboard Vendas - Supervisão'

    dados = DashboardVendasSupervisao()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-supervisao.html', contexto)


def relatorios_supervisao(request, fonte: str):
    fonte_relatorio = fonte
    if fonte_relatorio not in ('faturamentos', 'orcamentos', 'pedidos'):
        return HttpResponse("Pagina invalida", status=404)

    direito_exportar_emails = request.user.has_perm('analysis.export_contatosemails')

    titulo_pagina = 'Dashboard Vendas - Relatorios Supervisão'

    titulo_pagina_2 = f'Relatorios {fonte_relatorio}'

    contexto: Dict = {'titulo_pagina': titulo_pagina, 'titulo_pagina_2': titulo_pagina_2,
                      'fonte_relatorio': fonte_relatorio, 'direito_exportar_emails': direito_exportar_emails, }

    form = RelatoriosSupervisaoFaturamentosForm
    if fonte_relatorio == 'orcamentos':
        form = RelatoriosSupervisaoOrcamentosForm

    formulario = form()

    if request.method == 'GET' and request.GET:
        formulario = form(request.GET)
        if formulario.is_valid():
            if request.GET:
                dados = get_relatorios_vendas(fonte_relatorio, **formulario.cleaned_data)

                coluna_rentabilidade = formulario.cleaned_data.get('coluna_rentabilidade')
                coluna_rentabilidade_valor = formulario.cleaned_data.get('coluna_rentabilidade_valor')
                coluna_quantidade_documentos = formulario.cleaned_data.get('coluna_quantidade_documentos')

                valor_mercadorias_total = 0
                mc_total = 0
                mc_valor_total = 0
                quantidade_documentos_total = 0
                for dado in dados:
                    valor_mercadorias_total += dado.get('VALOR_MERCADORIAS', 0)  # type:ignore
                    if coluna_rentabilidade or coluna_rentabilidade_valor:
                        mc_valor_total += dado.get('MC_VALOR', 0)  # type:ignore
                    if coluna_quantidade_documentos:
                        quantidade_documentos_total += dado.get('QUANTIDADE_DOCUMENTOS', 0)  # type:ignore
                if mc_valor_total and valor_mercadorias_total:
                    mc_total = mc_valor_total / valor_mercadorias_total * 100

                totais = {
                    'VALOR MERCADORIAS': round(valor_mercadorias_total, 2),
                    'MC': round(mc_total, 2),
                    'MC VALOR': round(mc_valor_total, 2),
                    'QUANTIDADE DOCUMENTOS': round(quantidade_documentos_total, 0),
                }

                cabecalho = []
                if dados:
                    cabecalho = [chave.replace('_', ' ') for chave in dados[0].keys()]  # type:ignore

                contexto.update({
                    'dados': dados,
                    'cabecalho': cabecalho,
                    'valor_mercadorias_total': valor_mercadorias_total,
                    'mc_total': mc_total,
                    'mc_valor_total': mc_valor_total,
                    'quantidade_documentos_total': quantidade_documentos_total,
                    'totais': totais,
                })

            if 'exportar-submit' in request.GET:
                excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = f'relatorio_{fonte_relatorio}'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

            if 'exportar-emails-submit' in request.GET:
                chave_grupos = [f'(1, {dado['CHAVE_GRUPO_ECONOMICO']})' for dado in dados]
                chave_grupos = ', '.join(chave_grupos)
                condicao = '(1, CLIENTES.CHAVE_GRUPOECONOMICO) IN ({})'
                condicao = condicao.format(chave_grupos)
                emails = get_email_contatos(condicao)

                excel = arquivo_excel(emails, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'emails'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

    contexto.update({'formulario': formulario, })

    return render(request, 'dashboards/pages/relatorios-supervisao.html', contexto)


def indicadores(request):
    titulo_pagina = 'Indicadores'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormIndicadores()

    if request.method == 'GET' and request.GET:
        formulario = FormIndicadores(request.GET)
        if formulario.is_valid():
            indicador = formulario.cleaned_data.get('indicador')
            inicio = formulario.cleaned_data.get('inicio')
            fim = formulario.cleaned_data.get('fim')
            valores = formulario.cleaned_data.get('valores')
            frequencia = formulario.cleaned_data.get('frequencia')

            periodo = {}
            periodo.update({'periodo__data_inicio__gte': inicio}) if inicio else None
            periodo.update({'periodo__data_inicio__lte': fim}) if fim else None

            # Dados Totais

            dados = IndicadoresValores.objects.filter(indicador=indicador, **periodo)
            dados = dados.order_by('periodo__data_inicio')

            dados_grafico = dados.values('periodo__data_inicio', 'periodo__ano_referencia', 'valor_meta', 'valor_real')
            dados_grafico = pd.DataFrame(dados_grafico)
            dados_grafico = dados_grafico.rename(columns={'periodo__data_inicio': 'Periodo',
                                                          'periodo__ano_referencia': 'Ano',
                                                          'valor_meta': 'Meta', 'valor_real': 'Real'})

            if frequencia == 'anual':
                dados_grafico = dados_grafico.drop('Periodo', axis=1)
                dados_grafico = dados_grafico.rename(columns={'Ano': 'Periodo'})
                dados_grafico = dados_grafico.groupby('Periodo').sum().reset_index()

            dados_grafico['Real'] = dados_grafico['Real'].astype(float)
            dados_grafico['Meta'] = dados_grafico['Meta'].astype(float)
            dados_grafico['Meta %'] = 100
            dados_grafico.loc[dados_grafico['Meta'] == 0, 'Meta %'] = 0
            dados_grafico['Real %'] = dados_grafico['Real'] / dados_grafico['Meta'] * 100
            dados_grafico['Real %'] = dados_grafico['Real %'].fillna(0)
            dados_grafico['Real %'] = np.floor(dados_grafico['Real %']).astype(float)

            grafico_dados_html = ""
            if not dados_grafico.empty:
                y_total = ['Real %', 'Meta %'] if valores == 'proporcional' else ['Real', 'Meta']
                y_label = '%' if valores == 'proporcional' else 'R$'

                grafico_dados = px.line(dados_grafico, x='Periodo', y=y_total, title=f'{indicador} {y_label}',
                                        labels={'variable': 'Valores', 'value': y_label}, markers=True,)
                grafico_dados.update_layout(update_layout_kwargs)
                grafico_dados_html = pio.to_html(grafico_dados, full_html=False)

            # Dados por Carteira

            grafico_dados_carteiras_html = []
            if indicador.descricao == 'Meta Carteiras':  # type:ignore
                dados_carteiras = MetasCarteiras.objects.filter(indicador_valor__in=dados)
                dados_carteiras = dados_carteiras.order_by('indicador_valor__periodo__data_inicio')

                dados_carteiras_grafico = dados_carteiras.values('indicador_valor__periodo__data_inicio',
                                                                 'indicador_valor__periodo__ano_referencia',
                                                                 'vendedor__nome', 'responsavel__nome',
                                                                 'valor_meta', 'valor_real')
                dados_carteiras_grafico = pd.DataFrame(dados_carteiras_grafico)
                dados_carteiras_grafico = dados_carteiras_grafico.rename(columns={'indicador_valor__periodo__data_inicio': 'Periodo',
                                                                                  'indicador_valor__periodo__ano_referencia': 'Ano',
                                                                                  'vendedor__nome': 'Carteira',
                                                                                  'responsavel__nome': 'Responsavel',
                                                                                  'valor_meta': 'Meta',
                                                                                  'valor_real': 'Real'})

                if frequencia == 'anual':
                    dados_carteiras_grafico = dados_carteiras_grafico.drop(['Periodo', 'Responsavel'], axis=1)
                    dados_carteiras_grafico = dados_carteiras_grafico.rename(columns={'Ano': 'Periodo'})
                    dados_carteiras_grafico = dados_carteiras_grafico.groupby(
                        ['Periodo', 'Carteira']).sum().reset_index()

                dados_carteiras_grafico['Real'] = dados_carteiras_grafico['Real'].astype(float)
                dados_carteiras_grafico['Meta'] = dados_carteiras_grafico['Meta'].astype(float)
                dados_carteiras_grafico['Meta %'] = 100
                dados_carteiras_grafico.loc[dados_carteiras_grafico['Meta'] == 0, 'Meta %'] = 0
                dados_carteiras_grafico['Real %'] = dados_carteiras_grafico['Real'] / \
                    dados_carteiras_grafico['Meta'] * 100
                dados_carteiras_grafico['Real %'] = dados_carteiras_grafico['Real %'].fillna(0)
                dados_carteiras_grafico['Real %'] = np.floor(dados_carteiras_grafico['Real %']).astype(float)

                if frequencia == 'mensal':
                    dados_carteiras_grafico['Responsavel'] = dados_carteiras_grafico['Responsavel'].fillna('Ninguem')

                carteiras = list(dados_carteiras_grafico['Carteira'].unique())
                carteiras = sorted(carteiras)

                y_carteira = ['Real %'] if valores == 'proporcional' else ['Real']
                for carteira in carteiras:
                    dados_carteira_grafico = dados_carteiras_grafico[dados_carteiras_grafico['Carteira'] == carteira]
                    y_carteira_2 = dados_carteira_grafico['Meta %'] if valores == 'proporcional' else dados_carteira_grafico['Meta']

                    custom_data = None
                    hover_template = ''
                    color = None
                    if frequencia == 'mensal':
                        custom_data = dados_carteira_grafico[['Responsavel']]
                        hover_template = 'Responsável: %{customdata[0]}<br>'
                        color = 'Responsavel'

                    grafico_dados_carteira = px.line(dados_carteira_grafico, x='Periodo', y=y_carteira,
                                                     color=color, markers=True,
                                                     title=f'META {carteira} {y_label}',
                                                     labels={'variable': 'Valores', 'value': y_label},)
                    grafico_dados_carteira.add_trace(go.Scatter(
                        x=dados_carteira_grafico['Periodo'],
                        y=y_carteira_2,
                        customdata=custom_data,
                        mode='lines+markers',
                        name=f'Meta {y_label}',
                        line_color='black',
                        hovertemplate=f'{hover_template}' + 'Período: %{x}<br>' +
                        f'{y_label}' + ': %{y:,.2s}<extra></extra>'
                    ))
                    grafico_dados_carteira.update_layout(update_layout_kwargs)
                    grafico_dados_carteira_html = pio.to_html(grafico_dados_carteira, full_html=False)

                    grafico_dados_carteiras_html.append(grafico_dados_carteira_html)

            contexto.update({'grafico_dados_html': grafico_dados_html,
                             'grafico_dados_carteiras_html': grafico_dados_carteiras_html})

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/indicadores.html', contexto)
