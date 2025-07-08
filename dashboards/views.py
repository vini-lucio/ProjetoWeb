from typing import Dict, Literal
from django.shortcuts import render
from django.http import HttpResponse
from .services import (DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_vendas, get_email_contatos,
                       DashboardVendasCarteira, eventos_dia_atrasos, confere_orcamento)
from .forms import (RelatoriosSupervisaoFaturamentosForm, RelatoriosSupervisaoOrcamentosForm,
                    FormDashboardVendasCarteiras, FormAnaliseOrcamentos)
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario, arquivo_excel_response
from utils.data_hora_atual import data_x_dias
from utils.base_forms import FormVendedoresMixIn
from utils.cor_rentabilidade import get_cores_rentabilidade
import pandas as pd


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
                                                             incluir_orcamentos_oportunidade=True,
                                                             **carteira_parametros)
                excel = arquivo_excel(orcamentos_em_aberto, cabecalho_negrito=True, formatar_numero=(['H', 'I'], 2),
                                      formatar_data=['B', 'C'], ajustar_largura_colunas=True)
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

    formulario = FormAnaliseOrcamentos()

    if request.method == 'GET' and request.GET:
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
                contexto.update({'dados': dados, 'confere_orcamento': confere})

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/analise_orcamentos.html', contexto)


def eventos_dia(request):
    titulo_pagina = 'Eventos do Dia'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormVendedoresMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormVendedoresMixIn(request.GET)
        if formulario.is_valid():
            carteira = formulario.cleaned_data.get('carteira')
            carteira_nome = carteira.nome if carteira else '%%'
            contexto['titulo_pagina'] += f' {carteira_nome}' if carteira_nome != '%%' else ' Todos'

            dados = eventos_dia_atrasos(carteira=carteira_nome)

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


def listagens(request, listagem: str):
    if listagem not in ('sumidos', 'nuncamais', 'presentes', 'potenciais',):
        return HttpResponse("Pagina invalida", status=404)

    titulo_pagina = f'Os {listagem}'

    contexto: dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormVendedoresMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormVendedoresMixIn(request.GET)
        if formulario.is_valid():
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

            descricao_listagem = ''
            if listagem == 'sumidos':
                descricao_listagem = 'Grupos que compravam com frequencia e não compram a 6 meses'
                inicio = data_x_dias(180 + 365, passado=True)
                fim = data_x_dias(180, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=3,
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'presentes':
                descricao_listagem = 'Grupos que compram quase todo mês e não compram a 2 meses'
                inicio = data_x_dias(60 + 180, passado=True)
                fim = data_x_dias(60, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=3,
                                              **parametros_comuns, **carteira_parametros)

            if listagem == 'nuncamais':
                descricao_listagem = 'Grupos que compravam com frequencia e não compram a 2 anos'
                inicio = None
                fim = data_x_dias(730, passado=True)
                dados = get_relatorios_vendas(fonte='faturamentos', inicio=inicio, fim=fim,
                                              quantidade_meses_maior_que=9,
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
    if fonte_relatorio not in ('faturamentos', 'orcamentos'):
        return HttpResponse("Pagina invalida", status=404)

    direito_exportar_emails = request.user.has_perm('analysis.export_contatosemails')

    titulo_pagina = 'Dashboard Vendas - Relatorios Supervisão'

    titulo_pagina_2 = 'Relatorios Faturamentos'
    if fonte_relatorio == 'orcamentos':
        titulo_pagina_2 = 'Relatorios Orçamentos'

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
                    valor_mercadorias_total += dado.get('VALOR_MERCADORIAS')  # type:ignore
                    if coluna_rentabilidade or coluna_rentabilidade_valor:
                        mc_valor_total += dado.get('MC_VALOR')  # type:ignore
                    if coluna_quantidade_documentos:
                        quantidade_documentos_total += dado.get('QUANTIDADE_DOCUMENTOS')  # type:ignore
                if mc_valor_total and valor_mercadorias_total:
                    mc_total = mc_valor_total / valor_mercadorias_total * 100

                contexto.update({
                    'dados': dados,
                    'valor_mercadorias_total': valor_mercadorias_total,
                    'mc_total': mc_total,
                    'mc_valor_total': mc_valor_total,
                    'quantidade_documentos_total': quantidade_documentos_total,
                })

            if 'exportar-submit' in request.GET:
                excel = arquivo_excel(dados, cabecalho_negrito=True, ajustar_largura_colunas=True)
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'relatorio_faturamentos'
                if fonte_relatorio == 'orcamentos':
                    nome_arquivo = 'relatorio_orcamentos'
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
