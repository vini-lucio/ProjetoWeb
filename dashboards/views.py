from typing import Dict, Literal
from django.shortcuts import render
from django.http import HttpResponse
from .services import (DashboardVendasTv, DashboardVendasSupervisao, get_relatorios_vendas, get_email_contatos,
                       DashboardVendasCarteira, eventos_dia_atrasos)
from .forms import (RelatoriosSupervisaoFaturamentosForm, RelatoriosSupervisaoOrcamentosForm,
                    FormDashboardVendasCarteiras)
from utils.exportar_excel import arquivo_excel, salvar_excel_temporario, arquivo_excel_response


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
                dashboard_vendas_carteira = DashboardVendasCarteira(carteira=carteira_nome)
                dados = dashboard_vendas_carteira.get_dados()

                fonte: Literal['orcamentos', 'pedidos',
                               'faturamentos'] = formulario.cleaned_data.get('fonte')  # type: ignore
                em_aberto: bool = formulario.cleaned_data.get(
                    'em_aberto') if fonte != 'faturamentos' else False  # type: ignore
                inicio = formulario.cleaned_data.get('inicio') if not em_aberto else None
                fim = formulario.cleaned_data.get('fim') if not em_aberto else None

                valores_periodo = get_relatorios_vendas(fonte=fonte, inicio=inicio, fim=fim, coluna_data_emissao=True,
                                                        coluna_status_documento=True,
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
                orcamentos_em_aberto = get_relatorios_vendas(fonte='orcamentos', coluna_data_emissao=True,
                                                             status_documento_em_aberto=True, coluna_documento=True,
                                                             coluna_cliente=True, coluna_data_entrega_itens=True,
                                                             coluna_orcamento_oportunidade=True,
                                                             incluir_orcamentos_oportunidade=True,
                                                             **carteira_parametros)
                excel = arquivo_excel(orcamentos_em_aberto, cabecalho_negrito=True, ajustar_largura_colunas=True,
                                      formatar_numero=(['F'], 2))
                arquivo = salvar_excel_temporario(excel)
                nome_arquivo = 'ORCAMENTOS_EM_ABERTO'
                nome_arquivo += f'_{carteira_nome}' if carteira_nome != '%%' else '_TODOS'
                response = arquivo_excel_response(arquivo, nome_arquivo)
                return response

            if 'exportar-eventos-submit' in request.GET:
                eventos = eventos_dia_atrasos(carteira=carteira_nome)
                if eventos:
                    excel = arquivo_excel(eventos, cabecalho_negrito=True, ajustar_largura_colunas=True,
                                          formatar_numero=(['F'], 2))
                    arquivo = salvar_excel_temporario(excel)
                    nome_arquivo = 'EVENTOS'
                    nome_arquivo += f'_{carteira_nome}' if carteira_nome != '%%' else '_TODOS'
                    response = arquivo_excel_response(arquivo, nome_arquivo)
                    return response

    contexto.update({'formulario': formulario})

    return render(request, 'dashboards/pages/vendas-carteira.html', contexto)


def vendas_tv(request):
    titulo_pagina = 'Dashboard Vendas - TV'

    dashboard_vendas_tv = DashboardVendasTv()
    dados = dashboard_vendas_tv.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-tv.html', contexto)


def vendas_supervisao(request):
    titulo_pagina = 'Dashboard Vendas - Supervisão'

    dashboard_vendas_supervisao = DashboardVendasSupervisao()
    dados = dashboard_vendas_supervisao.get_dados()

    contexto = {'titulo_pagina': titulo_pagina, 'dados': dados}

    return render(request, 'dashboards/pages/vendas-supervisao.html', contexto)


# TODO: forçar somente usuarios do grupo de supervisao ou direito especifico
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
