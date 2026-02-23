from typing import Dict, Literal
from django.shortcuts import render
from django.http import HttpResponse
from .models import IndicadoresValores, MetasCarteiras
from .services import (DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_vendas, get_email_contatos,
                       DashboardVendasCarteira, eventos_dia_atrasos, confere_orcamento, eventos_em_aberto_por_dia,
                       get_relatorios_financeiros, confere_inscricoes_estaduais)
from .services_estoque import DashBoardEstoque
from .services_marketing import DashBoardMarketing
from .forms import (RelatoriosSupervisaoFaturamentosForm, RelatoriosSupervisaoOrcamentosForm,
                    FormDashboardVendasCarteiras, FormAnaliseOrcamentos, FormEventos, FormListagensVendas,
                    FormIndicadores, RelatoriosFinanceirosForm, FormDashboardMarketing)
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario, arquivo_excel_response
from utils.data_hora_atual import data_x_dias
from utils.base_forms import FormVendedoresMixIn, FormVendedoresNonRequiredMixIn
from utils.cor_rentabilidade import get_cores_rentabilidade
from utils.plotly_parametros import update_layout_kwargs
from utils.site_setup import get_site_setup
import pandas as pd
import numpy as np


def vendas_carteira(request):
    """Retorna dados para pagina de dashboard de vendas por carteira, baseado nos filtros do formulario.

    Retorno:
    --------
    :HttpResponse: com pagina renderizada ou download de arquivo excel

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormDashboardVendasCarteiras): com o formulario

    Se o formulario estiver valido:

    :dados (DashboardVendasCarteira): com os dados de venda de acordo com o formulario
    :valores_periodo (list[dict]): com a lista de documentos de acordo com o formulario
    :valor_total (float): somatoria de valor mercadorias em valores_periodo
    :valor_liquidados (float): somatoria de valor mercadorias em valores_periodo de orçamentos / pedidos liquidados
    :valor_em_abertos (float): somatoria de valor mercadorias em valores_periodo de orçamentos / pedidos não oportunidade em aberto ou bloqueados
    :valor_perdidos (float): somatoria de valor mercadorias em valores_periodo de orçamentos perdidos
    :valor_oportunidades_em_aberto (float): somatoria de valor mercadorias em valores_periodo de orçamentos oportunidade em aberto ou bloqueados
    :valor_devolucoes (float): somatoria de valor mercadorias em valores_periodo de faturamentos de devoluções"""
    titulo_pagina = 'Dashboard Vendas'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormDashboardVendasCarteiras()

    if request.method == 'GET' and request.GET:
        formulario = FormDashboardVendasCarteiras(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Total'

            carteira_parametros = carteira.carteira_parametros() if carteira else {}

            if 'atualizar-submit' in request.GET:
                dados = DashboardVendasCarteira(carteira=carteira_nome)

                fonte: Literal['orcamentos', 'pedidos',
                               'faturamentos'] = formulario.cleaned_data.get('fonte')  # type: ignore
                em_aberto: bool = formulario.cleaned_data.get(
                    'em_aberto') if fonte != 'faturamentos' else False  # type: ignore
                inicio = formulario.cleaned_data.get('inicio') if not em_aberto else None
                fim = formulario.cleaned_data.get('fim') if not em_aberto else None

                # TODO: filtrar pela legenda? Em aberto, perdido e liquidado (status) e por oportunidade
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
    """Retorna dados de rentabilidade e desconto reais e sugeridos dos itens de um orçamento para pagina de
    analise de orçamentos em dashboard de vendas por carteira.

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormAnaliseOrcamentos): com o formulario
    :cores_rentabilidade (dict): com a porcentagem da margem de contribuição (lucro + despesa fixa) por cor

    Se o formulario estiver valido:

    :dados (list[dict]): com os dados de rentabilidade e descontos dos itens do orçamento do formulario
    :confere_orcamento (list[dict]): com a lista de erros do orçamento do formulario
    :confere_inscricoes_estaduais (list[dict]): com a lista de erros de inscrição estadual do orçamento do formulario"""
    titulo_pagina = 'Analise Orçamento'

    cores_rentabilidade = get_cores_rentabilidade()
    cores_rentabilidade.update({'verde': cores_rentabilidade['verde'] + cores_rentabilidade['despesa_adm']})
    cores_rentabilidade.update({'amarelo': cores_rentabilidade['amarelo'] + cores_rentabilidade['despesa_adm']})
    cores_rentabilidade.update({'vermelho': cores_rentabilidade['vermelho'] + cores_rentabilidade['despesa_adm']})

    contexto: dict = {'titulo_pagina': titulo_pagina, 'cores_rentabilidade': cores_rentabilidade, }

    # forçar estar logado para aparecer todas as opções de desconto (customização desfeita)
    # formulario = FormAnaliseOrcamentos(usuario=request.user)
    formulario = FormAnaliseOrcamentos()

    if request.method == 'GET' and request.GET:
        # forçar estar logado para aparecer todas as opções de desconto (customização desfeita)
        # formulario = FormAnaliseOrcamentos(request.GET, usuario=request.user)
        formulario = FormAnaliseOrcamentos(request.GET)
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

                # Atualização no dfe obrigando login no gov para algumas consultas em 10/10/2025 para impedir acessos automaticos
                # confere_ie = []
                confere_ie = confere_inscricoes_estaduais('orcamentos', {'documento': orcamento})  # type:ignore

                contexto.update({'dados': dados, 'confere_orcamento': confere,
                                 'confere_inscricoes_estaduais': confere_ie})

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/analise_orcamentos.html', contexto)


def detalhes_dia(request):
    """Retorna dados de detalhes de vendas por familia de produto por carteira para pagina de detalhes em
    dasboard de vendas por carteira (do mes definido em site setup).

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormVendedoresNonRequiredMixIn): com o formulario

    Se o formulario estiver valido:

    :dados (list[dict]): com os dados de vendas por familia de produto por carteira do formulario"""
    titulo_pagina = 'Detalhes'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormVendedoresNonRequiredMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormVendedoresNonRequiredMixIn(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            carteira_parametros = carteira.carteira_parametros() if carteira else {}  # type:ignore

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
    """Retorna dados para pagina de eventos de vendas por carteira, baseado nos filtros do formulario.

    Retorno:
    --------
    :HttpResponse: com pagina renderizada ou download de arquivo excel

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormEventos): com o formulario

    Se o formulario estiver valido:

    :dados (list[dict]): com os dados de eventos por carteira de acordo com o formulario"""
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
    """Retorna dados para pagina de eventos por dia por carteira com a quantidade de eventos em aberto por dia,
    baseado nos filtros do formulario.

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormVendedoresMixIn): com o formulario

    Se o formulario estiver valido:

    :dados (list[dict]): com a quantidade de eventos em aberto por dia por carteira de acordo com o formulario"""
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
    """Retorna dados para pagina de listagens de vendas por carteira, baseado nos filtros do formulario.

    Parametros:
    -----------
    :listagem (str): com qual relatorio será exibido, podendo ser 'sumidos', 'nuncamais', 'presentes' ou 'potenciais'

    Retorno:
    --------
    :HttpResponse: com pagina renderizada ou download de arquivo excel

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormListagensVendas): com o formulario

    Se o formulario estiver valido:

    :dados (list[dict]): com os dados de venda de acordo com o parametro de listagem e formulario
    :descricao_listagem (str): com uma breve descrição da listagem selecionada"""
    if listagem not in ('sumidos', 'nuncamais', 'presentes', 'potenciais',):
        return HttpResponse("Pagina invalida", status=404)

    titulo_pagina = f'Os {listagem}'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormListagensVendas()

    if request.method == 'GET' and request.GET:
        formulario = FormListagensVendas(request.GET)
        if formulario.is_valid():
            desconsiderar_futuros = formulario.cleaned_data.get('desconsiderar_futuros')
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            carteira_parametros = carteira.carteira_parametros() if carteira else {}

            parametros_comuns = {'coluna_media_dia': True, 'coluna_grupo_economico': True, 'coluna_carteira': True,
                                 'coluna_tipo_cliente': True, 'coluna_quantidade_meses': True,
                                 'status_cliente_ativo': True, 'ordenar_valor_descrescente_prioritario': True,
                                 'nao_compraram_depois': True, 'desconsiderar_justificativas': True,
                                 'considerar_itens_excluidos': True, }

            tipo_cliente = formulario.cleaned_data.get('tipo_cliente')
            if tipo_cliente:
                parametros_comuns.update({'tipo_cliente': tipo_cliente})

            if desconsiderar_futuros:
                parametros_comuns.update({'desconsiderar_grupo_economico_com_evento_futuro': True})

            descricao_listagem = ''
            if listagem == 'sumidos':
                descricao_listagem = 'Grupos que compravam com frequencia (em 1 ano) e não compram a 6 meses (sem orçamento em aberto)'
                inicio = data_x_dias(180 + 365, passado=True)
                fim = data_x_dias(180, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=2,  # originalmente 3
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'presentes':
                descricao_listagem = 'Grupos que compram quase todo mês (em 6 meses) e não compram a 2 meses (sem orçamento em aberto)'
                inicio = data_x_dias(60 + 180, passado=True)
                fim = data_x_dias(60, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=2,  # originalmente 3
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'nuncamais':
                descricao_listagem = 'Grupos que compravam com frequencia (desde sempre) e não compram a 2 anos (sem orçamento em aberto)'
                inicio = None
                fim = data_x_dias(730, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=7,  # originalmente 9
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'potenciais':
                descricao_listagem = 'Grupos que perdem mais que compram nos ultimos 2 anos (sem orçamento em aberto)'
                inicio = data_x_dias(1 + 730, passado=True)
                fim = data_x_dias(1, passado=True)

                fechados = get_relatorios_vendas(fonte='orcamentos', inicio=inicio, fim=fim,
                                                 status_produto_orcamento_tipo='FECHADO',
                                                 **parametros_comuns, **carteira_parametros)
                perdidos = get_relatorios_vendas(fonte='orcamentos', inicio=inicio, fim=fim,
                                                 status_produto_orcamento_tipo='PERDIDO_CANCELADO',
                                                 **parametros_comuns, **carteira_parametros)

                dt_fechados = pd.DataFrame(fechados)
                if not dt_fechados.empty:
                    dt_fechados.drop(columns=['QUANTIDADE_MESES', 'MEDIA_DIA'], inplace=True)
                    dt_fechados.rename(columns={'VALOR_MERCADORIAS': 'VALOR_FECHADOS'}, inplace=True)

                    dt_perdidos = pd.DataFrame(perdidos)

                    dt_dados = pd.merge(dt_fechados, dt_perdidos, how='outer', on=['CHAVE_GRUPO_ECONOMICO', 'GRUPO',
                                                                                   'CARTEIRA', 'TIPO_CLIENTE']).fillna(0)
                    dt_dados = dt_dados.loc[dt_dados['VALOR_MERCADORIAS'] > dt_dados['VALOR_FECHADOS']]
                    dt_dados = dt_dados.loc[dt_dados['VALOR_MERCADORIAS'] >= 10000]
                    dt_dados = dt_dados.sort_values('VALOR_MERCADORIAS', ascending=False)
                else:
                    dt_dados = dt_fechados

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
    """Retorna dados para pagina de dashboard de vendas tv"""
    titulo_pagina = 'Dashboard Vendas - TV'

    dados = DashboardVendasTv()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)


def vendas_supervisao(request):
    """Retorna dados para pagina de dashboard de vendas supervisão"""
    titulo_pagina = 'Dashboard Vendas - Supervisão'

    dados = DashboardVendasSupervisao()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-supervisao.html', contexto)


def relatorios_supervisao(request, fonte: str):
    """Retorna dados para pagina de relatorios de supervisão de vendas, baseado nos filtros do formulario.

    Parametros:
    -----------
    :fonte (str): com qual relatorio será exibido, podendo ser 'faturamentos', 'orcamentos' ou 'pedidos'

    Retorno:
    --------
    :HttpResponse: com pagina renderizada ou download de arquivo excel

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :titulo_pagina_2 (str): com segundo titulo baseado no parametro fonte
    :fonte_relatorio (str): com o mesmo do parametro fonte
    :direito_exportar_emails (bool): com o booleano se o usuario possui o direiro de exportar os emails dos contatos do relatorio
    :formulario (RelatoriosSupervisaoFaturamentosForm ou RelatoriosSupervisaoOrcamentosForm): com o formulario baseado no parametro fonte

    Se o formulario estiver valido:

    :dados (list[dict]): com os dados de venda de acordo com o formulario
    :cabecalho (list[str]): com as chaves de dados, trocando '_' por espaços
    :valor_mercadorias_total (float): somatoria de valor mercadorias em dados
    :mc_valor_total (float): somatoria de valor de margem de contribuição em dados
    :mc_total (float): proporção entre mc_valor_total e valor_mercadorias_total
    :quantidade_documentos_total (float): somatoria de quantidade de documento em dados
    :totais (dict): com os numeros arredondados de valor_mercadorias_total, mc_valor_total, mc_total e quantidade_documentos_total"""
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
                # Para burlar o limite de 1000 na lista da clausula IN do oracle, fazer comparação composta (1, campo) IN ((1, busca), ...)
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


def relatorios_financeiros(request):
    """Retorna dados para pagina de relatorios financeiros, baseado nos filtros do formulario.

    Retorno:
    --------
    :HttpResponse: com pagina renderizada ou download de arquivo excel

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (RelatoriosFinanceirosForm): com o formulario

    Se o formulario estiver valido:

    :dados_dados (list[tuple[str, list[dict]]]): com os dados financeiros de acordo com o formulario. Onde o primeiro
    elemento da tupla é a fonte dos dados pagar, receber ou saldo (resto dos dois anteriores), o segundo elemento
    é a lista de dict dos dados financeiros.

    :cabecalho (list[str]): com as chaves da lista de dict da tupla em dados_dados, trocando '_' por espaços"""
    titulo_pagina = 'Relatorios Financeiros'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    formulario = RelatoriosFinanceirosForm()

    if request.method == 'GET' and request.GET:
        formulario = RelatoriosFinanceirosForm(request.GET)
        if formulario.is_valid():
            if request.GET:
                dados_dados = []
                cabecalho = []

                dados_receber = get_relatorios_financeiros('receber', **formulario.cleaned_data)
                df_dados_receber = pd.DataFrame(dados_receber)
                if dados_receber:
                    cabecalho_receber = [chave.replace('_', ' ') for chave in dados_receber[0].keys()]  # type:ignore
                    cabecalho = cabecalho_receber

                    dados_receber_totais = pd.DataFrame([df_dados_receber.sum(numeric_only=True)])
                    dados_receber_totais = pd.concat([df_dados_receber, dados_receber_totais],
                                                     ignore_index=True).fillna('')
                    dados_dados.append(('Receber', dados_receber_totais.to_dict(orient='records')))

                dados_pagar = get_relatorios_financeiros('pagar', valor_debito_negativo=True,
                                                         **formulario.cleaned_data)
                df_dados_pagar = pd.DataFrame(dados_pagar)
                if dados_pagar:
                    cabecalho_pagar = [chave.replace('_', ' ') for chave in dados_pagar[0].keys()]  # type:ignore
                    cabecalho = cabecalho_pagar

                    dados_pagar_totais = pd.DataFrame([df_dados_pagar.sum(numeric_only=True)])
                    dados_pagar_totais = pd.concat([df_dados_pagar, dados_pagar_totais], ignore_index=True).fillna('')
                    dados_dados.append(('Pagar', dados_pagar_totais.to_dict(orient='records')))

                if not df_dados_receber.empty and not df_dados_pagar.empty:
                    saldo = pd.concat([dados_receber_totais.tail(1), dados_pagar_totais.tail(1)], ignore_index=False)
                    saldo = pd.DataFrame([saldo.sum()])
                    dados_dados.append(('Saldo', saldo.to_dict(orient='records')))

                contexto.update({
                    'dados_dados': dados_dados,
                    'cabecalho': cabecalho,
                })

            if 'exportar-submit' in request.GET:
                dados = pd.concat([df_dados_receber, df_dados_pagar])
                dados = dados.to_dict(orient='records')

                excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'relatorio_financeiros'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

    contexto.update({'formulario': formulario, })

    return render(request, 'dashboards/pages/relatorios-financeiros.html', contexto)


def indicadores(request):
    """Retorna dados para pagina de indicadores, baseado nos filtros do formulario.

    Contexto:
    ---------
    :titulo_pagina (str): com o titulo da pagina
    :formulario (FormIndicadores): com o formulario

    Se o formulario estiver valido:

    :grafico_dados_html (str): com o html do grafico do total do indicador de acordo com o formulario
    :grafico_dados_carteiras_html (str): com o html do grafico do indicador por carteira de acordo com o formulario"""
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

            # Grafico Total

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

                # Grafico por Carteira

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


def marketing_leads(request):
    """Retorna dados para pagina de dashboard de marketing de leads do RD Station."""
    titulo_pagina = 'Dashboard Leads Marketing'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormDashboardMarketing()

    if request.method == 'GET' and request.GET:
        formulario = FormDashboardMarketing(request.GET)
        if formulario.is_valid():
            inicio = formulario.cleaned_data.get('inicio')
            fim = formulario.cleaned_data.get('fim')
            fechado_inicio = formulario.cleaned_data.get('fechado_inicio')
            fechado_fim = formulario.cleaned_data.get('fechado_fim')
            dados = DashBoardMarketing(inicio, fim, fechado_inicio, fechado_fim)

            contexto.update({'dados': dados, })

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/marketing-leads.html', contexto)


def estoque(request):
    """Retorna dados para pagina de dashboard de estoque."""
    titulo_pagina = 'Dashboard Estoque'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    if request.method == 'GET' and request.GET:
        dados = DashBoardEstoque(com_sugestao=True)
        contexto.update({'com_sugestao': True, })
    else:
        dados = DashBoardEstoque()

    contexto.update({'dados': dados, })

    return render(request, 'dashboards/pages/estoque.html', contexto)
