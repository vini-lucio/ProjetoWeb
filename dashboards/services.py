from typing import Literal
from analysis.models import STATUS_ORCAMENTOS_ITENS
from dashboards.services_financeiro import get_relatorios_financeiros
from utils.custom import DefaultDict
from utils.converter import somente_digitos
from utils.oracle.conectar import executar_oracle
from utils.data_hora_atual import data_hora_atual, hoje, data_x_dias
from utils.cor_rentabilidade import cor_rentabilidade_css, falta_mudar_cor_mes
from utils.site_setup import (get_site_setup, get_assistentes_tecnicos, get_assistentes_tecnicos_agenda,
                              get_transportadoras, get_consultores_tecnicos_ativos)
from utils.lfrete import notas as lfrete_notas, orcamentos as lfrete_orcamentos, pedidos as lfrete_pedidos
from utils.perdidos_justificativas import justificativas
from frete.services import get_dados_pedidos_em_aberto, get_transportadoras_valores_atendimento
from home.services import frete_cif_ano_mes_a_mes, faturado_bruto_ano_mes_a_mes
from home.models import Vendedores, InscricoesEstaduais
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import IntegerField
from django.db.models.functions import Cast
from datetime import datetime
import pandas as pd


class DashBoardVendas():
    def __init__(self, carteira='%%', executar_completo: bool = True,
                 dados_pedidos_mes_entrega_mes_dias: pd.DataFrame | None = None,
                 dados_pedidos_fora_mes_entrega_mes: pd.DataFrame | None = None,
                 dados_desvolucoes_mes: pd.DataFrame | None = None,
                 ) -> None:
        self.carteira = carteira
        self.vendedor = None
        self.site_setup = get_site_setup()
        parametro_carteira = {}
        if self.site_setup:
            self.dias_meta = self.site_setup.dias_uteis_mes_as_float
            self.dias_meta_reais = self.site_setup.dias_uteis_mes_reais_as_float
            self.primeiro_dia_mes = self.site_setup.primeiro_dia_mes_as_ddmmyyyy
            self.primeiro_dia_util_mes = self.site_setup.primeiro_dia_util_mes_as_ddmmyyyy
            self.ultimo_dia_mes = self.site_setup.ultimo_dia_mes_as_ddmmyyyy
            self.primeiro_dia_util_proximo_mes = self.site_setup.primeiro_dia_util_proximo_mes_as_ddmmyyyy

            if self.carteira == '%%':
                self.meta_diaria = self.site_setup.meta_diaria_as_float
                self.meta_diaria_real = self.site_setup.meta_diaria_real_as_float
                self.meta_mes = self.site_setup.meta_mes_as_float
            else:
                self.vendedor = Vendedores.objects.get(nome=self.carteira)
                parametro_carteira = {'carteira': self.vendedor}
                if self.vendedor.nome == 'PAREDE DE CONCRETO':
                    parametro_carteira = {'carteira_parede_de_concreto': True}
                if self.vendedor.nome == 'PREMOLDADO / POSTE':
                    parametro_carteira = {'carteira_premoldado_poste': True}
                self.meta_mes = float(self.vendedor.meta_mes)
                self.meta_diaria = self.meta_mes / self.dias_meta if self.dias_meta else 0.0
                self.meta_diaria_real = self.meta_mes / self.dias_meta_reais if self.dias_meta_reais else 0.0

        self.dias_decorridos = dias_decorridos(
            self.site_setup.primeiro_dia_mes, self.site_setup.ultimo_dia_mes)  # type:ignore
        self.meta_acumulada_dia_real = self.dias_decorridos * self.meta_diaria_real

        if dados_pedidos_mes_entrega_mes_dias is None:
            pedidos_mes_entrega_mes_dias = get_relatorios_vendas('pedidos',
                                                                 inicio=self.site_setup.primeiro_dia_mes,  # type:ignore
                                                                 fim=self.site_setup.ultimo_dia_mes,  # type:ignore
                                                                 coluna_data_emissao=True,
                                                                 data_entrega_itens_menor_igual=self.site_setup.primeiro_dia_util_proximo_mes,  # type:ignore
                                                                 coluna_peso_produto_proprio=True,
                                                                 coluna_rentabilidade_cor=True,
                                                                 coluna_carteira=True,
                                                                 **parametro_carteira)
            pedidos_mes_entrega_mes_dias = pd.DataFrame(pedidos_mes_entrega_mes_dias)
        else:
            pedidos_mes_entrega_mes_dias = dados_pedidos_mes_entrega_mes_dias

        if dados_pedidos_fora_mes_entrega_mes is None:
            pedidos_fora_mes_entrega_mes = get_relatorios_vendas('pedidos',
                                                                 data_emissao_menor_que=self.site_setup.primeiro_dia_mes,  # type:ignore
                                                                 data_entrega_itens_maior_que=self.site_setup.primeiro_dia_util_mes,  # type:ignore
                                                                 data_entrega_itens_menor_igual=self.site_setup.primeiro_dia_util_proximo_mes,  # type:ignore
                                                                 coluna_peso_produto_proprio=True,
                                                                 coluna_rentabilidade_cor=True,
                                                                 coluna_carteira=True,
                                                                 **parametro_carteira)
            pedidos_fora_mes_entrega_mes = pd.DataFrame(pedidos_fora_mes_entrega_mes)
        else:
            pedidos_fora_mes_entrega_mes = dados_pedidos_fora_mes_entrega_mes

        if dados_desvolucoes_mes is None:
            desvolucoes_mes = get_relatorios_vendas('faturamentos',
                                                    inicio=self.site_setup.primeiro_dia_mes,  # type:ignore
                                                    fim=self.site_setup.ultimo_dia_mes,  # type:ignore
                                                    especie='E',
                                                    coluna_peso_produto_proprio=True,
                                                    coluna_rentabilidade_cor=True,
                                                    coluna_carteira=True,
                                                    **parametro_carteira)
            desvolucoes_mes = pd.DataFrame(desvolucoes_mes)
        else:
            desvolucoes_mes = dados_desvolucoes_mes

        self.pedidos_mes_entrega_mes_dias = pedidos_mes_entrega_mes_dias.copy()
        self.pedidos_fora_mes_entrega_mes = pedidos_fora_mes_entrega_mes.copy()
        self.desvolucoes_mes = desvolucoes_mes.copy()

        self.media_dia_pedido_mes_entrega_mes_sem_hoje = 0.0
        if not pedidos_mes_entrega_mes_dias.empty:
            dias_decorridos_sem_hoje = self.dias_decorridos - 1 if self.dias_decorridos else 0.0
            pedidos_mes_entrega_mes_dias_sem_hoje = pedidos_mes_entrega_mes_dias[pedidos_mes_entrega_mes_dias['DATA_EMISSAO'].dt.date != hoje(
            )]
            valor_total_mes_sem_hoje = float(pedidos_mes_entrega_mes_dias_sem_hoje['VALOR_MERCADORIAS'].sum())
            self.media_dia_pedido_mes_entrega_mes_sem_hoje = valor_total_mes_sem_hoje / dias_decorridos_sem_hoje \
                if dias_decorridos_sem_hoje else 0.0

            pedidos_mes_entrega_mes_dias = pedidos_mes_entrega_mes_dias.drop(columns=['CARTEIRA'])
        if not pedidos_fora_mes_entrega_mes.empty:
            pedidos_fora_mes_entrega_mes = pedidos_fora_mes_entrega_mes.drop(columns=['CARTEIRA'])
        if not desvolucoes_mes.empty:
            desvolucoes_mes = desvolucoes_mes.drop(columns=['CARTEIRA'])

        pedidos_mes_entrega_mes_total = pd.DataFrame()
        if not pedidos_mes_entrega_mes_dias.empty:
            pedidos_mes_entrega_mes_total = pedidos_mes_entrega_mes_dias.drop(columns=['DATA_EMISSAO'])
        total_mes = pd.concat([desvolucoes_mes, pedidos_fora_mes_entrega_mes, pedidos_mes_entrega_mes_total],
                              ignore_index=True)
        total_mes = pd.DataFrame([total_mes.sum(axis=0)])
        if not total_mes.empty:
            total_mes['MC_COR'] = total_mes['MC_VALOR_COR'] / total_mes['VALOR_MERCADORIAS'] * 100
        total_mes = total_mes.fillna(0).to_dict(orient='records')
        total_mes = total_mes[0] if total_mes else {'MC_VALOR_COR': 0,
                                                    'MC_COR': 0, 'PESO_PP': 0, 'VALOR_MERCADORIAS': 0}

        total_dia = pd.DataFrame()
        if not pedidos_mes_entrega_mes_dias.empty:
            total_dia = pedidos_mes_entrega_mes_dias[pedidos_mes_entrega_mes_dias['DATA_EMISSAO'].dt.date == hoje()]
        if not total_dia.empty:
            total_dia = total_dia.drop(columns=['DATA_EMISSAO'])
            total_dia = pd.DataFrame([total_dia.sum(axis=0)])
            total_dia['MC_COR'] = total_dia['MC_VALOR_COR'] / total_dia['VALOR_MERCADORIAS'] * 100
        total_dia = total_dia.to_dict(orient='records')
        total_dia = total_dia[0] if total_dia else {'MC_VALOR_COR': 0,
                                                    'MC_COR': 0, 'PESO_PP': 0, 'VALOR_MERCADORIAS': 0}

        self.total_dia = total_dia
        self.rentabilidade_pedidos_dia = self.total_dia['MC_COR']
        self.toneladas_dia = self.total_dia['PESO_PP'] / 1000
        self.pedidos_dia = self.total_dia['VALOR_MERCADORIAS']

        self.porcentagem_mc_dia = self.rentabilidade_pedidos_dia
        self.porcentagem_meta_dia = int(self.pedidos_dia / self.meta_diaria * 100) if self.meta_diaria else 0
        self.faltam_meta_dia = round(self.meta_diaria - self.pedidos_dia, 2)

        self.conversao_de_orcamentos = 0.0
        if executar_completo:
            self.conversao_de_orcamentos = conversao_de_orcamentos(parametro_carteira)
        self.faltam_abrir_orcamentos_dia = round(
            self.faltam_meta_dia / (self.conversao_de_orcamentos / 100), 2) if self.conversao_de_orcamentos else 0.0

        self.total_mes = total_mes
        self.rentabilidade_pedidos_mes_mc_mes = self.total_mes['MC_VALOR_COR']
        self.rentabilidade_pedidos_mes_rentabilidade_mes = self.total_mes['MC_COR']
        self.toneladas_mes = self.total_mes['PESO_PP'] / 1000
        self.pedidos_mes = self.total_mes['VALOR_MERCADORIAS']

        self.porcentagem_mc_mes = self.rentabilidade_pedidos_mes_rentabilidade_mes
        self.porcentagem_meta_mes = int(self.pedidos_mes / self.meta_mes * 100) if self.meta_mes else 0
        self.faltam_meta_mes = round(self.meta_mes - self.pedidos_mes, 2)
        self.cor_rentabilidade_css_dia = cor_rentabilidade_css(self.rentabilidade_pedidos_dia, True)
        self.cor_rentabilidade_css_mes = cor_rentabilidade_css(self.rentabilidade_pedidos_mes_rentabilidade_mes, True)

        self.falta_mudar_cor_mes = (0.0, 0.0, 0.0, '')
        if executar_completo:
            self.falta_mudar_cor_mes = falta_mudar_cor_mes(self.rentabilidade_pedidos_mes_mc_mes,
                                                           self.pedidos_mes,
                                                           self.rentabilidade_pedidos_mes_rentabilidade_mes)
        self.falta_mudar_cor_mes_valor = round(self.falta_mudar_cor_mes[0], 2)
        self.falta_mudar_cor_mes_valor_rentabilidade = round(self.falta_mudar_cor_mes[1], 2)
        self.falta_mudar_cor_mes_porcentagem = round(self.falta_mudar_cor_mes[2], 2)
        self.falta_mudar_cor_mes_cor = self.falta_mudar_cor_mes[3]

        self.meta_em_dia = self.pedidos_mes - self.meta_acumulada_dia_real

        self.data_hora_atual = data_hora_atual()

        self.confere_pedidos = []
        self.confere_inscricoes_estaduais = []
        if executar_completo:
            self.confere_pedidos = confere_pedidos(self.carteira, parametro_carteira)
            self.confere_inscricoes_estaduais = confere_inscricoes_estaduais('pedidos', parametro_carteira)


class DashboardVendasCarteira(DashBoardVendas):
    def __init__(self, carteira='%%', executar_completo: bool = True,
                 dados_pedidos_mes_entrega_mes_dias: pd.DataFrame | None = None,
                 dados_pedidos_fora_mes_entrega_mes: pd.DataFrame | None = None,
                 dados_desvolucoes_mes: pd.DataFrame | None = None,) -> None:
        super().__init__(carteira, executar_completo, dados_pedidos_mes_entrega_mes_dias,
                         dados_pedidos_fora_mes_entrega_mes, dados_desvolucoes_mes)

        self.recebido, self.a_receber = (0.0, 0.0)
        if executar_completo:
            self.recebido, self.a_receber = recebido_a_receber(self.site_setup.primeiro_dia_mes,  # type:ignore
                                                               self.site_setup.ultimo_dia_mes,  # type:ignore
                                                               self.vendedor)


class DashboardVendasTv(DashBoardVendas):
    def __init__(self) -> None:
        super().__init__()
        self.assistentes_tecnicos = get_assistentes_tecnicos()
        self.agenda_vec = get_assistentes_tecnicos_agenda()


class DashboardVendasSupervisao(DashBoardVendas):
    def __init__(self) -> None:
        super().__init__()
        faturado_bruto = faturado_bruto_ano_mes_a_mes(mes_atual=True)
        try:
            faturado_bruto = faturado_bruto['FATURADO_TOTAL']  # type:ignore
        except TypeError:
            faturado_bruto = 0

        frete_cif = frete_cif_ano_mes_a_mes(mes_atual=True)
        try:
            frete_cif = frete_cif['AGILLI'] + frete_cif['OUTRAS_TRANSPORTADORAS']  # type:ignore
        except TypeError:
            frete_cif = 0
        frete_cif = 0 if faturado_bruto == 0 else frete_cif / faturado_bruto * 100

        self.frete_cif = frete_cif
        self.carteiras = []
        for carteira in get_consultores_tecnicos_ativos():
            dados = {}
            if carteira.nome not in ('PAREDE DE CONCRETO', 'PREMOLDADO / POSTE'):
                dados_desvolucoes_mes = self.desvolucoes_mes
                if not dados_desvolucoes_mes.empty:
                    dados_desvolucoes_mes = self.desvolucoes_mes[self.desvolucoes_mes['CARTEIRA'] == carteira.nome]

                dados.update({
                    'dados_pedidos_mes_entrega_mes_dias': self.pedidos_mes_entrega_mes_dias[self.pedidos_mes_entrega_mes_dias['CARTEIRA'] == carteira.nome],
                    'dados_pedidos_fora_mes_entrega_mes': self.pedidos_fora_mes_entrega_mes[self.pedidos_fora_mes_entrega_mes['CARTEIRA'] == carteira.nome],
                    'dados_desvolucoes_mes': dados_desvolucoes_mes,
                })
            self.carteiras.append(DashboardVendasCarteira(carteira.nome, executar_completo=False, **dados))


def carteira_mapping(carteira):
    carteira_actions_mapping = {
        'PREMOLDADO / POSTE': {
            'carteira': "%%",
            'filtro_nao_carteira': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND"
        },
        'PAREDE DE CONCRETO': {
            'carteira': "%%",
            'filtro_nao_carteira': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND"
        }
    }

    filtro_nao_carteira = ""
    if carteira in carteira_actions_mapping:
        filtro_nao_carteira = carteira_actions_mapping[carteira]['filtro_nao_carteira']
        carteira = carteira_actions_mapping[carteira]['carteira']

    return carteira, filtro_nao_carteira


def recebido_a_receber(primeiro_dia_mes, ultimo_dia_mes, carteira) -> tuple[float, float]:
    """Valor recebido e a receber dos titulos com valor comercial no mes"""
    recebido = 0.0
    a_receber = 0.0

    parametro_carteira = carteira.carteira_parametros() if carteira else {}
    notas = get_relatorios_vendas('faturamentos', coluna_chave_documento=True, coluna_valor_bruto=True,
                                  data_vencimento_titulo_entre=[primeiro_dia_mes, ultimo_dia_mes], **parametro_carteira)
    notas = pd.DataFrame(notas)

    if notas.empty:
        return float(recebido), float(a_receber)

    notas['PROPORCAO_MERCADORIAS'] = notas['VALOR_MERCADORIAS'] / notas['VALOR_BRUTO']
    notas = notas[['CHAVE_DOCUMENTO', 'PROPORCAO_MERCADORIAS']]

    receber = get_relatorios_financeiros('receber', data_vencimento_inicio=primeiro_dia_mes,
                                         data_vencimento_fim=ultimo_dia_mes, coluna_valor_titulo=True,
                                         coluna_chave_nota=True, coluna_data_vencimento=True,)
    receber = pd.DataFrame(receber)
    receber = receber[['CHAVE_NOTA', 'DATA_VENCIMENTO', 'VALOR_TITULO']]

    total = pd.merge(notas, receber, how='inner', left_on='CHAVE_DOCUMENTO', right_on='CHAVE_NOTA')
    total['VALOR_TITULO_MERCADORIAS'] = total['VALOR_TITULO'] * total['PROPORCAO_MERCADORIAS']
    total = total[['DATA_VENCIMENTO', 'VALOR_TITULO_MERCADORIAS']]

    recebido = total[(total['DATA_VENCIMENTO'].dt.date >= primeiro_dia_mes) & (
        total['DATA_VENCIMENTO'].dt.date <= hoje())]
    recebido = recebido['VALOR_TITULO_MERCADORIAS'].sum()

    a_receber = total[(total['DATA_VENCIMENTO'].dt.date > hoje()) & (
        total['DATA_VENCIMENTO'].dt.date <= ultimo_dia_mes)]
    a_receber = a_receber['VALOR_TITULO_MERCADORIAS'].sum()

    return float(recebido), float(a_receber)


def dias_decorridos(primeiro_dia_mes, ultimo_dia_mes) -> float:
    """Quantidade de dias com orçamentos no mes"""
    resultado = get_relatorios_vendas('pedidos', inicio=primeiro_dia_mes, fim=ultimo_dia_mes,
                                      coluna_dias_decorridos=True)
    resultado = resultado[0].get('DIAS_DECORRIDOS', 0.00) if resultado else 0.00

    return float(resultado)


def conversao_de_orcamentos(parametro_carteira: dict):
    """Taxa de conversão de orçamentos com valor comercial dos ultimos 90 dias, ignorando orçamentos oportunidade e palavras chave de erros internos"""
    inicio = data_x_dias(90, passado=True)
    fim = data_x_dias(0, passado=True)

    total = get_relatorios_vendas('orcamentos', inicio=inicio, fim=fim, considerar_itens_excluidos=True,
                                  desconsiderar_justificativas=True, **parametro_carteira)
    total = total[0]
    total = total['VALOR_MERCADORIAS'] if total else 0

    status_fechado = STATUS_ORCAMENTOS_ITENS.get_status_fechado()
    fechado = get_relatorios_vendas('orcamentos', inicio=inicio, fim=fim, considerar_itens_excluidos=True,
                                    desconsiderar_justificativas=True, status_produto_orcamento=status_fechado,
                                    **parametro_carteira)
    fechado = fechado[0]
    fechado = fechado['VALOR_MERCADORIAS'] if fechado else 0

    conversao = fechado / total * 100 if total else 0

    return float(conversao)


def confere_inscricoes_estaduais(fonte, parametro_carteira: dict = {}, parametro_documento: dict = {}):
    inscricoes = get_relatorios_vendas(fonte, coluna_estado=True, coluna_cgc=True, coluna_inscricao_estadual=True,
                                       coluna_carteira=True, coluna_documento=True,
                                       status_documento_em_aberto=True,
                                       incluir_sem_valor_comercial=True, incluir_orcamentos_oportunidade=True,
                                       **parametro_carteira, **parametro_documento)

    erros = []
    for inscricao in inscricoes:
        cgc_cadastro = inscricao['CGC']
        carteira = inscricao['CARTEIRA']
        pedido = inscricao['DOCUMENTO']
        inscricao_cadastro = inscricao['INSCRICAO_ESTADUAL']
        inscricao_cadastro_digitos = somente_digitos(inscricao_cadastro) if inscricao_cadastro else None
        uf_cadastro = inscricao['UF_PRINCIPAL']

        if not cgc_cadastro:
            continue

        inscricoes_api = InscricoesEstaduais.objects.filter(cnpj=cgc_cadastro)

        if not inscricoes_api.exists():
            continue

        # inscrição correta
        inscricao_valida = inscricoes_api.filter(inscricao_estadual=inscricao_cadastro_digitos,
                                                 estado__sigla=uf_cadastro, habilitado=True)
        if inscricao_valida.exists():
            continue

        # estados que podem ter inscrição com 0 a esquerda, mas não são obrigados a ter:
        if uf_cadastro in ['AM', 'BA', 'CE', 'MT', 'PE', 'RS'] and inscricao_cadastro_digitos:
            inscricao_cadastro_digitos_int = int(inscricao_cadastro_digitos)
            inscricao_valida = inscricoes_api.annotate(inscricao_estadual_int=Cast('inscricao_estadual',
                                                                                   IntegerField()))
            inscricao_valida = inscricao_valida.filter(inscricao_estadual_int=inscricao_cadastro_digitos_int,
                                                       estado__sigla=uf_cadastro, habilitado=True)

            if inscricao_valida.exists():
                continue

        # api e cadastro isento de inscrição
        isento_api = inscricoes_api.first()
        if isento_api:
            isento_api = True if not isento_api.inscricao_estadual else False
            if isento_api and not inscricao_cadastro_digitos:
                continue

        # api sem inscrição habilitada no estado e cadastro isento de inscrição
        inscricao_valida = inscricoes_api.filter(estado__sigla=uf_cadastro, habilitado=True)
        if not inscricao_valida.exists() and not inscricao_cadastro_digitos:
            continue

        inscricao['ERRO'] = 'CONFERIR INSCRICAO ESTADUAL'
        inscricao['CONSULTOR'] = carteira
        inscricao['PEDIDO'] = pedido
        erros.append(inscricao)

    return erros


def confere_orcamento(orcamento: int = 0) -> list | None:
    """Confere possiveis erros de um orçamento em aberto"""
    sql = """
        SELECT
            *

        FROM
            (
                SELECT DISTINCT
                    ORCAMENTOS.NUMPED AS ORCAMENTO,
                    VENDEDORES.NOMERED AS CONSULTOR,
                    CASE
                        WHEN CLIENTES.ENDERECO LIKE ' %' THEN 'ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO LIKE '% ' THEN 'ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DO CLIENTE EM BRANCO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.FONE1 NOT LIKE '______%' OR CLIENTES.FONE1 LIKE '%I%' OR CLIENTES.FONE1 LIKE '%D%' OR CLIENTES.FONE1 LIKE '%R%' OR CLIENTES.FONE1 LIKE '%*%' THEN 'TELEFONE 1 DO CLIENTE INCORRETO'
                        WHEN ORCAMENTOS.PEDCLI LIKE ' %' THEN 'PEDIDO DO CLIENTE NO ORCAMENTO COM ESPACO NO INICIO'
                        WHEN ORCAMENTOS.PEDCLI LIKE '% ' THEN 'PEDIDO DO CLIENTE NO ORCAMENTO COM ESPACO NO FIM'
                        WHEN ORCAMENTOS.FORMA_FATURAMENTO = 'DUPLICATA' AND CLIENTES.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DO CLIENTE DESMARCADO'
                        WHEN ORCAMENTOS.FORMA_FATURAMENTO = 'DUPLICATA' AND ORCAMENTOS.BOLETO_NF = 'NAO' THEN 'CAMPO ENVIAR BOLETO JUNTAMENTE COM A NF NO ORCAMENTO DESMARCADO'
                        WHEN ORCAMENTOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '% %' OR CLIENTES_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '.%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%.' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR CLIENTES_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DO CLIENTE INCORRETO'
                        WHEN NFE_NAC_CLI_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_CLI_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_CLI_EMAILS.EMAIL IS NULL THEN 'EMAIL DE ENVIO DA NFE DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE ' %' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE '% ' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE ' %' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE '% ' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT IS NULL THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE EM BRANCO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT LIKE ' %' THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT LIKE '% ' THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT IS NULL THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE EM BRANCO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.CEP_ENT NOT LIKE '________' THEN 'CEP DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.TIPO IS NULL AND PLATAFORMAS.RAZAO_SOCIAL IS NOT NULL THEN 'TIPO/CNPJ DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORCAMENTOS.FORMA_FATURAMENTO = 'DUPLICATA' AND ORDEM_CLIENTE.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DA ORDEM DESMARCADO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE ' %' THEN 'ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE '% ' THEN 'ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DA ORDEM EM BRANCO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND (ORDEM_CLIENTE.FONE1 NOT LIKE '______%' OR ORDEM_CLIENTE.FONE1 LIKE '%I%' OR ORDEM_CLIENTE.FONE1 LIKE '%D%' OR ORDEM_CLIENTE.FONE1 LIKE '%R%' OR ORDEM_CLIENTE.FONE1 LIKE '%*%') THEN 'TELEFONE 1 DA ORDEM INCORRETO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND ORCAMENTOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (ORDEM_EMAILS_BOLETOS.EMAIL LIKE '% %' OR ORDEM_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '.%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%.' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR ORDEM_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DA ORDEM INCORRETO'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND (NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_ORDEM_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_ORDEM_EMAILS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DA NFE DA ORDEM INCORRETO'
                        WHEN TRANSPORTADORAS.EMAIL_NFE LIKE '% %' OR TRANSPORTADORAS.EMAIL_NFE NOT LIKE '%_@_%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%,%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%>%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%<%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '.%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%.' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%..%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%""%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%(%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%)%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%;%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%\\%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%[%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%]%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%!%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%#%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%$%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%*%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%/%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%?%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%|%' THEN 'EMAIL DE ENVIO DA NFE DA TRANSPORTADORA INCORRETO'
                        WHEN ORCAMENTOS.TEXTO1 LIKE '%–%' OR ORCAMENTOS.TEXTO2 LIKE '%–%' OR ORCAMENTOS.TEXTO3 LIKE '%–%' OR ORCAMENTOS.TEXTO4 LIKE '%–%' OR ORCAMENTOS.TEXTO5 LIKE '%–%' OR ORCAMENTOS.TEXTO6 LIKE '%–%' THEN 'CARACTERES INVALIDOS NOS TEXTOS LEGAIS'
                        WHEN ORCAMENTOS.DESTINO != ORCAMENTOS_ITENS.DESTINO_MERCADORIAS THEN 'DESTINO DAS MERCADORIAS DA CAPA DO ORMANENTO E A DOS ITENS ESTAO DIFERENTES'
                        WHEN CLIENTES.ISENTO_INSCRICAO = 'SIM' AND CLIENTES.INDICADOR_IE != 9 OR CLIENTES.ISENTO_INSCRICAO = 'NAO' AND CLIENTES.INDICADOR_IE != 1 THEN 'INDICADOR DA INSCRICAO ESTADUAL DO CLIENTE INCORRETA'
                        WHEN ORCAMENTOS.CHAVE_TIPO = 32 AND CLIENTES.ISENTO_INSCRICAO != 'NAO' OR ORCAMENTOS.CHAVE_TIPO = 51 AND CLIENTES.ISENTO_INSCRICAO != 'SIM' THEN 'TIPO DE ORCAMENTO INCORRETO'
                        -- WHEN (ORCAMENTOS.COBRANCA_FRETE = 0 AND ORCAMENTOS.VALOR_FRETE != 0) OR (ORCAMENTOS.COBRANCA_FRETE = 1 AND ORCAMENTOS.VALOR_FRETE = 0) OR (ORCAMENTOS.COBRANCA_FRETE = 2 AND (ORCAMENTOS.VALOR_FRETE != 0 OR ORCAMENTOS.VALOR_FRETE_EMPRESA != 0)) OR ORCAMENTOS.COBRANCA_FRETE = 3 OR (ORCAMENTOS.COBRANCA_FRETE = 4 AND (ORCAMENTOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR ORCAMENTOS.VALOR_FRETE != 0 OR ORCAMENTOS.VALOR_FRETE_EMPRESA != 0)) OR (ORCAMENTOS.COBRANCA_FRETE = 5 AND (ORCAMENTOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR ORCAMENTOS.VALOR_FRETE = 0 OR ORCAMENTOS.VALOR_FRETE_EMPRESA != 0)) OR (ORCAMENTOS.COBRANCA_FRETE = 6 AND (ORCAMENTOS.CHAVE_TRANSPORTADORA NOT IN (7738, 8012) OR ORCAMENTOS.VALOR_FRETE != 0 OR ORCAMENTOS.VALOR_FRETE_EMPRESA != 0)) OR ORCAMENTOS.COBRANCA_FRETE = 9 THEN 'CONTRATACAO DE FRETE INCORRETO'
                        WHEN CLIENTES.EMAIL_NFE_SEM_ANEXOS = 'SIM' THEN 'CLIENTE MARCADO PARA NAO INCLUIR ANEXOS NO EMAIL DA NFE'
                        -- WHEN CONTATOS.FONEC IS NULL AND CONTATOS.CELULAR IS NULL THEN 'CONTATO DE ENTREGA DO ORCAMENTO SEM NUMERO'
                        WHEN ORCAMENTOS.CHAVE_TIPO IN (47, 71, 12, 36) AND (PRODUTOS.CHAVE_FAMILIA != 8378 AND PRODUTOS.PESO_LIQUIDO != PRODUTOS.CUBAGEM OR PRODUTOS.CHAVE_FAMILIA = 8378 AND PRODUTOS.CUBAGEM = 0) THEN 'INFORMAR TI, PESO ESPECIFICO INCORRETO'
                        -- WHEN ORCAMENTOS.PEDCLI IS NULL OR ORCAMENTOS.PEDCLI NOT LIKE '%____%' OR (ORCAMENTOS.PEDCLI IS NULL AND ORCAMENTOS_ITENS.PEDCLI IS NOT NULL AND ORCAMENTOS_ITENS.PEDCLI NOT LIKE '%____%') THEN 'PEDIDO DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.UF_ENT != CLIENTES.UF AND PLATAFORMAS.CNPJ_CPF = CLIENTES.CGC AND PLATAFORMAS.INSCRICAO = CLIENTES.INSCRICAO THEN 'INSCRICAO ESTADUAL DO ENDERECO DE ENTREGA INCORRETA'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.TIPO IS NOT NULL AND PLATAFORMAS.CNPJ_CPF IS NULL THEN 'CNPJ/CPF DO ENDERECO DE ENTREGA INCORRETO'
                        -- WHEN TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND ORCAMENTOS.COBRANCA_FRETE IN (0, 1, 4, 5) AND (ORCAMENTOS.VALOR_FRETE_EMPRESA IS NULL OR ORCAMENTOS.VALOR_FRETE_EMPRESA = 0) THEN 'PREENCHER VALOR FRETE COPLAS/EMPRESA'
                        WHEN CLIENTES.CHAVE_TIPO IN (7908, 7904, 7911) AND PRODUTOS.CODIGO LIKE '%TAMPAO%' AND PRODUTOS.CODIGO NOT LIKE '%CLARO%' THEN 'TROCAR PARA TAMPAO CLARO'
                    END AS ERRO

                FROM
                    COPLAS.CONTATOS,
                    COPLAS.ORCAMENTOS_ITENS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.NFE_NAC_CLI_EMAILS) NFE_NAC_ORDEM_EMAILS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.CLIENTES_EMAILS_BOLETOS) ORDEM_EMAILS_BOLETOS,
                    (SELECT CODCLI, ENDERECO, ENDERECO_NUMERO, ENDERECO_COMPLEMENTO, FONE1, ENVIAR_BOLETO_PDF FROM COPLAS.CLIENTES) ORDEM_CLIENTE,
                    COPLAS.PLATAFORMAS,
                    COPLAS.NFE_NAC_CLI_EMAILS,
                    COPLAS.CLIENTES_EMAILS_BOLETOS,
                    COPLAS.VENDEDORES,
                    COPLAS.TRANSPORTADORAS,
                    COPLAS.ORCAMENTOS,
                    COPLAS.CLIENTES,
                    COPLAS.PRODUTOS

                WHERE
                    ORCAMENTOS.CHAVE_CONTATO_ENTREGA = CONTATOS.CHAVE(+) AND
                    ORCAMENTOS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
                    NFE_NAC_ORDEM_EMAILS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_EMAILS_BOLETOS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_CLIENTE.CODCLI(+) = ORCAMENTOS.CHAVE_CLIENTE_REMESSA AND
                    ORCAMENTOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
                    CLIENTES.CODCLI = NFE_NAC_CLI_EMAILS.CHAVE_CLIENTE(+) AND
                    CLIENTES.CODCLI = CLIENTES_EMAILS_BOLETOS.CHAVE_CLIENTE(+) AND
                    VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                    ORCAMENTOS.CHAVE_TRANSPORTADORA = TRANSPORTADORAS.CODTRANSP AND
                    ORCAMENTOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND

                    ORCAMENTOS.STATUS != 'LIQUIDADO' AND
                    ORCAMENTOS.NUMPED = :orcamento
            )

        WHERE
            ERRO IS NOT NULL
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, orcamento=orcamento)

    if not resultado:
        return []

    return resultado


def confere_pedidos(carteira: str = '%%', parametro_carteira: dict = {}) -> list | None:
    """Confere possiveis erros dos pedidos em aberto"""
    sql = """
        SELECT
            *

        FROM
            (
                SELECT DISTINCT
                    PEDIDOS.NUMPED AS PEDIDO,
                    VENDEDORES.NOMERED AS CONSULTOR,
                    CASE
                        WHEN CLIENTES.ENDERECO LIKE ' %' THEN 'ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO LIKE '% ' THEN 'ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DO CLIENTE EM BRANCO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO INICIO'
                        WHEN CLIENTES.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CLIENTE COM ESPACO NO FIM'
                        WHEN CLIENTES.FONE1 NOT LIKE '______%' OR CLIENTES.FONE1 LIKE '%I%' OR CLIENTES.FONE1 LIKE '%D%' OR CLIENTES.FONE1 LIKE '%R%' OR CLIENTES.FONE1 LIKE '%*%' THEN 'TELEFONE 1 DO CLIENTE INCORRETO'
                        WHEN PEDIDOS.PEDCLI LIKE ' %' THEN 'PEDIDO DO CLIENTE NO PEDIDO COM ESPACO NO INICIO'
                        WHEN PEDIDOS.PEDCLI LIKE '% ' THEN 'PEDIDO DO CLIENTE NO PEDIDO COM ESPACO NO FIM'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND CLIENTES.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DO CLIENTE DESMARCADO'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND PEDIDOS.BOLETO_NF = 'NAO' THEN 'CAMPO ENVIAR BOLETO JUNTAMENTE COM A NF NO PEDIDO DESMARCADO'
                        WHEN PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '% %' OR CLIENTES_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '.%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%.' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR CLIENTES_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR CLIENTES_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DO CLIENTE INCORRETO'
                        WHEN NFE_NAC_CLI_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_CLI_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_CLI_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_CLI_EMAILS.EMAIL IS NULL THEN 'EMAIL DE ENVIO DA NFE DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE ' %' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_ENT LIKE '% ' THEN 'ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE ' %' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT LIKE '% ' THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_NUMERO_ENT IS NULL THEN 'NUMERO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE EM BRANCO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.ENDERECO_COMPLEMENTO_ENT LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT LIKE ' %' THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO INICIO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT LIKE '% ' THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE COM ESPACO NO FIM'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.BAIRRO_ENT IS NULL THEN 'BAIRRO DO ENDERECO DO CANTEIRO DE ENTREGA DO CLIENTE EM BRANCO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.CEP_ENT NOT LIKE '________' THEN 'CEP DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.TIPO IS NULL AND PLATAFORMAS.RAZAO_SOCIAL IS NOT NULL THEN 'TIPO/CNPJ DO CANTEIRO DE ENTREGA INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND ORDEM_CLIENTE.ENVIAR_BOLETO_PDF = 'NAO' THEN 'CAMPO ENVIAR BOLETO POR EMAIL DA ORDEM DESMARCADO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE ' %' THEN 'ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO LIKE '% ' THEN 'ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE ' %' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO LIKE '% ' THEN 'NUMERO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_NUMERO IS NULL THEN 'NUMERO DO ENDERECO DA ORDEM EM BRANCO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE ' %' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO INICIO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND ORDEM_CLIENTE.ENDERECO_COMPLEMENTO LIKE '% ' THEN 'COMPLEMENTO DO ENDERECO DA ORDEM COM ESPACO NO FIM'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND (ORDEM_CLIENTE.FONE1 NOT LIKE '______%' OR ORDEM_CLIENTE.FONE1 LIKE '%I%' OR ORDEM_CLIENTE.FONE1 LIKE '%D%' OR ORDEM_CLIENTE.FONE1 LIKE '%R%' OR ORDEM_CLIENTE.FONE1 LIKE '%*%') THEN 'TELEFONE 1 DA ORDEM INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND PEDIDOS.FORMA_FATURAMENTO = 'DUPLICATA' AND (ORDEM_EMAILS_BOLETOS.EMAIL LIKE '% %' OR ORDEM_EMAILS_BOLETOS.EMAIL NOT LIKE '%_@_%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%,%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%>%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%<%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '.%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%.' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%..%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%""%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%(%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%)%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%;%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%\\%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%[%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%]%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%!%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%#%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%$%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%*%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%/%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%?%' OR ORDEM_EMAILS_BOLETOS.EMAIL LIKE '%|%' OR ORDEM_EMAILS_BOLETOS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DO BOLETO DA NFE DA ORDEM INCORRETO'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND (NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '% %' OR NFE_NAC_ORDEM_EMAILS.EMAIL NOT LIKE '%_@_%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%,%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%>%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%<%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '.%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%.' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%..%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%""%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%(%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%)%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%;%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%\\%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%[%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%]%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%!%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%#%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%$%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%*%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%/%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%?%' OR NFE_NAC_ORDEM_EMAILS.EMAIL LIKE '%|%' OR NFE_NAC_ORDEM_EMAILS.EMAIL IS NULL) THEN 'EMAIL DE ENVIO DA NFE DA ORDEM INCORRETO'
                        WHEN TRANSPORTADORAS.EMAIL_NFE LIKE '% %' OR TRANSPORTADORAS.EMAIL_NFE NOT LIKE '%_@_%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%,%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%>%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%<%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '.%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%.' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%..%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%""%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%(%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%)%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%;%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%\\%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%[%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%]%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%!%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%#%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%$%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%*%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%/%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%?%' OR TRANSPORTADORAS.EMAIL_NFE LIKE '%|%' THEN 'EMAIL DE ENVIO DA NFE DA TRANSPORTADORA INCORRETO'
                        WHEN PEDIDOS.TEXTO1 LIKE '%–%' OR PEDIDOS.TEXTO2 LIKE '%–%' OR PEDIDOS.TEXTO3 LIKE '%–%' OR PEDIDOS.TEXTO4 LIKE '%–%' OR PEDIDOS.TEXTO5 LIKE '%–%' OR PEDIDOS.TEXTO6 LIKE '%–%' THEN 'CARACTERES INVALIDOS NOS TEXTOS LEGAIS'
                        WHEN PEDIDOS.DESTINO != PEDIDOS_ITENS.DESTINO_MERCADORIAS THEN 'DESTINO DAS MERCADORIAS DA CAPA DO ORMANENTO E A DOS ITENS ESTAO DIFERENTES'
                        WHEN CLIENTES.ISENTO_INSCRICAO = 'SIM' AND CLIENTES.INDICADOR_IE != 9 OR CLIENTES.ISENTO_INSCRICAO = 'NAO' AND CLIENTES.INDICADOR_IE != 1 THEN 'INDICADOR DA INSCRICAO ESTADUAL DO CLIENTE INCORRETA'
                        WHEN PEDIDOS.CHAVE_TIPO = 32 AND CLIENTES.ISENTO_INSCRICAO != 'NAO' OR PEDIDOS.CHAVE_TIPO = 51 AND CLIENTES.ISENTO_INSCRICAO != 'SIM' THEN 'TIPO DE PEDIDO INCORRETO'
                        WHEN (PEDIDOS.COBRANCA_FRETE = 0 AND PEDIDOS.VALOR_FRETE != 0) OR (PEDIDOS.COBRANCA_FRETE = 1 AND PEDIDOS.VALOR_FRETE = 0) OR (PEDIDOS.COBRANCA_FRETE = 2 AND (PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR PEDIDOS.COBRANCA_FRETE = 3 OR (PEDIDOS.COBRANCA_FRETE = 4 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR (PEDIDOS.COBRANCA_FRETE = 5 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (6766, 8069) OR PEDIDOS.VALOR_FRETE = 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR (PEDIDOS.COBRANCA_FRETE = 6 AND (PEDIDOS.CHAVE_TRANSPORTADORA NOT IN (7738, 8012) OR PEDIDOS.VALOR_FRETE != 0 OR PEDIDOS.VALOR_FRETE_EMPRESA != 0)) OR PEDIDOS.COBRANCA_FRETE = 9 THEN 'CONTRATACAO DE FRETE INCORRETO'
                        WHEN CLIENTES.EMAIL_NFE_SEM_ANEXOS = 'SIM' THEN 'CLIENTE MARCADO PARA NAO INCLUIR ANEXOS NO EMAIL DA NFE'
                        WHEN CONTATOS.FONEC IS NULL AND CONTATOS.CELULAR IS NULL THEN 'CONTATO DE ENTREGA DO PEDIDO SEM NUMERO'
                        WHEN PEDIDOS.CHAVE_TIPO IN (47, 71, 12, 36) AND (PRODUTOS.CHAVE_FAMILIA != 8378 AND PRODUTOS.PESO_LIQUIDO != PRODUTOS.CUBAGEM OR PRODUTOS.CHAVE_FAMILIA = 8378 AND PRODUTOS.CUBAGEM = 0) THEN 'INFORMAR TI, PESO ESPECIFICO INCORRETO'
                        WHEN PEDIDOS.PEDCLI IS NULL OR PEDIDOS.PEDCLI NOT LIKE '%____%' OR (PEDIDOS.PEDCLI IS NULL AND PEDIDOS_ITENS.PEDCLI IS NOT NULL AND PEDIDOS_ITENS.PEDCLI NOT LIKE '%____%') THEN 'PEDIDO DO CLIENTE INCORRETO'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.UF_ENT != CLIENTES.UF AND PLATAFORMAS.CNPJ_CPF = CLIENTES.CGC AND PLATAFORMAS.INSCRICAO = CLIENTES.INSCRICAO THEN 'INSCRICAO ESTADUAL DO ENDERECO DE ENTREGA INCORRETA'
                        WHEN PLATAFORMAS.ENTREGA_ALTERNATIVA = 'SIM' AND PLATAFORMAS.TIPO IS NOT NULL AND PLATAFORMAS.CNPJ_CPF IS NULL THEN 'CNPJ/CPF DO ENDERECO DE ENTREGA INCORRETO'
                        WHEN TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5) AND (PEDIDOS.VALOR_FRETE_EMPRESA IS NULL OR PEDIDOS.VALOR_FRETE_EMPRESA = 0) THEN 'PREENCHER VALOR FRETE COPLAS/EMPRESA'
                        WHEN PEDIDOS.CHAVE_TRANSPORTADORA = 6798 AND PEDIDOS.STATUS != 'BLOQUEADO' AND PEDIDOS.CHAVE_TIPO NOT IN (47, 71, 12, 36, 45) THEN 'TRANSPORTADORA INCORRETA'
                        WHEN CLIENTES.CHAVE_TIPO IN (7908, 7904, 7911) AND PEDIDOS.STATUS != 'BLOQUEADO' AND PRODUTOS.CODIGO LIKE '%TAMPAO%' AND PRODUTOS.CODIGO NOT LIKE '%CLARO%' THEN 'TROCAR PARA TAMPAO CLARO'
                    END AS ERRO

                FROM
                    COPLAS.CONTATOS,
                    COPLAS.PEDIDOS_ITENS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.NFE_NAC_CLI_EMAILS) NFE_NAC_ORDEM_EMAILS,
                    (SELECT CHAVE_CLIENTE, EMAIL FROM COPLAS.CLIENTES_EMAILS_BOLETOS) ORDEM_EMAILS_BOLETOS,
                    (SELECT CODCLI, ENDERECO, ENDERECO_NUMERO, ENDERECO_COMPLEMENTO, FONE1, ENVIAR_BOLETO_PDF FROM COPLAS.CLIENTES) ORDEM_CLIENTE,
                    COPLAS.PLATAFORMAS,
                    COPLAS.NFE_NAC_CLI_EMAILS,
                    COPLAS.CLIENTES_EMAILS_BOLETOS,
                    COPLAS.VENDEDORES,
                    COPLAS.TRANSPORTADORAS,
                    COPLAS.PEDIDOS,
                    COPLAS.CLIENTES,
                    COPLAS.PRODUTOS

                WHERE
                    PEDIDOS.CHAVE_CONTATO_ENTREGA = CONTATOS.CHAVE(+) AND
                    PEDIDOS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
                    PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
                    NFE_NAC_ORDEM_EMAILS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_EMAILS_BOLETOS.CHAVE_CLIENTE(+) = ORDEM_CLIENTE.CODCLI AND
                    ORDEM_CLIENTE.CODCLI(+) = PEDIDOS.CHAVE_CLIENTE_REMESSA AND
                    PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
                    CLIENTES.CODCLI = NFE_NAC_CLI_EMAILS.CHAVE_CLIENTE(+) AND
                    CLIENTES.CODCLI = CLIENTES_EMAILS_BOLETOS.CHAVE_CLIENTE(+) AND
                    VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
                    PEDIDOS.CHAVE_TRANSPORTADORA = TRANSPORTADORAS.CODTRANSP AND
                    PEDIDOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND

                    -- place holder para selecionar carteira
                    VENDEDORES.NOMERED LIKE :carteira AND

                    PEDIDOS.STATUS != 'LIQUIDADO'
                    -- PEDIDOS.DATA_PEDIDO >= TO_DATE('01/10/2024', 'DD-MM-YYYY')
            )

        WHERE
            ERRO IS NOT NULL
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, carteira=carteira)

    erros_atendimento_transportadoras = confere_pedidos_atendimento_transportadoras(parametro_carteira)
    if erros_atendimento_transportadoras:
        for erro_atendiemto_transportadoras in erros_atendimento_transportadoras:
            resultado.append(erro_atendiemto_transportadoras)

    if not resultado:
        return []

    return resultado


def confere_pedidos_atendimento_transportadoras(parametro_carteira: dict = {}) -> list | None:
    dados_pedidos = get_dados_pedidos_em_aberto(parametro_carteira)
    transportadoras = get_transportadoras()
    erros = []

    if not dados_pedidos:
        return []

    for dados_pedido in dados_pedidos:
        try:
            get_transportadoras_valores_atendimento(dados_orcamento_pedido=dados_pedido,
                                                    transportadora_orcamento_pedido=True)
        except ObjectDoesNotExist:
            transportadora = transportadoras.filter(chave_analysis=dados_pedido['CHAVE_TRANSPORTADORA'])
            if transportadora:
                pedido = dados_pedido['PEDIDO']
                consultor = dados_pedido['CARTEIRA']
                erro = 'TRANSPORTADORA NÃO ATENDE O DESTINO'
                erros.append({'PEDIDO': pedido, 'CONSULTOR': consultor, 'ERRO': erro})

    return erros


def eventos_dia_atrasos(carteira: str = '%%', incluir_futuros: bool = False) -> list | None:
    """Retorna eventos do dia e em atraso"""
    carteira, filtro_nao_carteira = carteira_mapping(carteira)

    periodo = "CLIENTES_HISTORICO.DATA <= TRUNC(SYSDATE) AND"
    if incluir_futuros:
        periodo = ""

    sql = """
        SELECT
            CLIENTES.CHAVE_GRUPOECONOMICO,
            CLIENTES.NOMERED,
            V_COLABORADORES.USUARIO,
            CLIENTES_HISTORICO.DATA,
            CLIENTES_HISTORICO.TIPO,

            CASE
                WHEN CLIENTES_HISTORICO.DATA < TRUNC(SYSDATE) AND CLIENTES_HISTORICO.TIPO = 'CONTATO' THEN '12 ATRASO'
                WHEN CLIENTES_HISTORICO.TIPO = 'ORCAMENTO' THEN '01 ORCAMENTOS'
                WHEN CLIENTES_HISTORICO.ASSUNTO LIKE '%ABITO DE COMPRA%' OR HABITO.CHAVE_CLIENTE IS NOT NULL THEN '02 HABITO COMPRA'
                WHEN CLIENTES_HISTORICO.TIPO = 'CONTATO' THEN '03 CONTATO'
                WHEN CLIENTES_HISTORICO.TIPO = 'REDE DE OBRAS' OR CLIENTES.CODCLI IN (SELECT DISTINCT CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CHAVE_CLIENTE = CLIENTES.CODCLI AND CHAVE_INFORMACAO IN (26, 27, 28)) THEN '04 REDE DE OBRAS'
                WHEN CLIENTES.CODCLI IN (SELECT DISTINCT CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CHAVE_CLIENTE = CLIENTES.CODCLI AND CHAVE_INFORMACAO IN (SELECT CHAVE FROM COPLAS.INFORMACOES_CLI WHERE DESCRICAO LIKE 'IC50%')) THEN '05 IC50+'
                WHEN CLIENTES_HISTORICO.TIPO = 'VISITA-OPORTUNIDADE' OR CLIENTES_HISTORICO.ASSUNTO LIKE '%VISITA_OPORTUNIDADE%' THEN '06 VISITA OPORT'
                WHEN CLIENTES_HISTORICO.TIPO = 'SOLICITACOES' THEN '07 SOLICITACOES'
                WHEN CLIENTES_HISTORICO.TIPO = 'VISITA-INFORMACAO' THEN '08 VISITA INF'
                WHEN CLIENTES_HISTORICO.TIPO = 'PESQ. DE SATISFACAO' THEN '09 SATISFACAO'
                WHEN CLIENTES_HISTORICO.TIPO = 'OBRA DE INFRA' OR CLIENTES.CODCLI IN (SELECT DISTINCT CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CHAVE_CLIENTE = CLIENTES.CODCLI AND CHAVE_INFORMACAO IN (8, 19)) THEN '10 INFRA'
                WHEN CLIENTES_HISTORICO.ASSUNTO LIKE '%OPORTUNIDADE%' OR CLIENTES_HISTORICO.ASSUNTO LIKE '%NOTICIA%' THEN '11 OPORT / NOTICIAS'
                WHEN CLIENTES_HISTORICO.TIPO = 'PROSPECCAO' THEN '13 PROSPECCAO'
                ELSE '14 OUTROS'
            END AS PRIORIDADE,

            CASE WHEN CLIENTES.CHAVE_GRUPOECONOMICO = 1 THEN NULL ELSE COALESCE(SUM(ORC.EM_ABERTO), 0) END AS ORC_EM_ABERTO,

            CASE
                WHEN CLIENTES.CHAVE_GRUPOECONOMICO = 1 THEN 'PESSOA FISICA'
                WHEN COALESCE(SUM(ORC.FECHADO), 0) > 0 AND COALESCE(SUM(ORC.NAO_FECHADO), 0) = 0 THEN '01 SEMPRE FECHA'
                WHEN COALESCE(SUM(ORC.FECHADO), 0) > 0 AND COALESCE(SUM(ORC.NAO_FECHADO), 0) > 0 THEN '02 PODE FECHAR MAIS'
                WHEN COALESCE(SUM(ORC.FECHADO), 0) = 0 AND COALESCE(SUM(ORC.NAO_FECHADO), 0) > 0 THEN '03 NORMALMENTE NAO FECHA'
                WHEN COALESCE(SUM(ORC.FECHADO), 0) = 0 AND COALESCE(SUM(ORC.NAO_FECHADO), 0) = 0 THEN '04 NAO ORCA'
            END AS CONDICAO

        FROM
            (
                SELECT DISTINCT
                    NOTAS.CHAVE_CLIENTE
                FROM
                    COPLAS.NOTAS

                WHERE
                    NOTAS.VALOR_COMERCIAL = 'SIM' AND
                    NOTAS.DATA_EMISSAO >= TRUNC(SYSDATE) - 180

                GROUP BY
                    NOTAS.CHAVE_CLIENTE

                HAVING
                    ((MAX(NOTAS.DATA_EMISSAO) - MIN(NOTAS.DATA_EMISSAO)) / SUM(1)) + MAX(NOTAS.DATA_EMISSAO) >= TRUNC(SYSDATE) - 14 AND
                    ((MAX(NOTAS.DATA_EMISSAO) - MIN(NOTAS.DATA_EMISSAO)) / SUM(1)) + MAX(NOTAS.DATA_EMISSAO) <= TRUNC(SYSDATE) + 14
            ) HABITO,
            (
                SELECT
                    CLIENTES.CHAVE_GRUPOECONOMICO,
                    ORCAMENTOS.STATUS,
                    SUM(CASE WHEN ORCAMENTOS.STATUS = 'EM ABERTO' THEN ORCAMENTOS.VALOR_TOTAL ELSE 0 END) AS EM_ABERTO,
                    SUM(CASE WHEN ORCAMENTOS.STATUS = 'LIQUIDADO' THEN ORCAMENTOS.VALOR_TOTAL ELSE 0 END) AS FECHADO,
                    SUM(CASE WHEN ORCAMENTOS.STATUS != 'EM ABERTO' AND ORCAMENTOS.STATUS != 'LIQUIDADO' THEN ORCAMENTOS.VALOR_TOTAL ELSE 0 END) AS NAO_FECHADO

                FROM
                    COPLAS.ORCAMENTOS,
                    COPLAS.CLIENTES

                WHERE
                    ORCAMENTOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND
                    ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND
                    CLIENTES.CHAVE_GRUPOECONOMICO != 1 AND
                    ORCAMENTOS.DATA_PEDIDO >= TRUNC(SYSDATE) - 365

                GROUP BY
                    CLIENTES.CHAVE_GRUPOECONOMICO,
                    ORCAMENTOS.STATUS
            ) ORC,
            COPLAS.VENDEDORES,
            COPLAS.V_COLABORADORES,
            COPLAS.CLIENTES_HISTORICO,
            COPLAS.CLIENTES

        WHERE
            CLIENTES.CODCLI = HABITO.CHAVE_CLIENTE(+) AND
            CLIENTES.CHAVE_GRUPOECONOMICO = ORC.CHAVE_GRUPOECONOMICO(+) AND
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES_HISTORICO.CHAVE_CLIENTE = CLIENTES.CODCLI AND
            CLIENTES_HISTORICO.CHAVE_RESPONSAVEL = V_COLABORADORES.CHAVE AND
            {periodo}
            CLIENTES_HISTORICO.DATA_REALIZADO IS NULL AND

            VENDEDORES.NOMERED LIKE :carteira AND
            {filtro_nao_carteira}

            1=1

        GROUP BY
            CLIENTES.CHAVE_GRUPOECONOMICO,
            CLIENTES.CODCLI,
            CLIENTES.NOMERED,
            VENDEDORES.NOMERED,
            V_COLABORADORES.USUARIO,
            CLIENTES_HISTORICO.DATA,
            CLIENTES_HISTORICO.TIPO,
            CLIENTES_HISTORICO.ASSUNTO,
            CLIENTES.CHAVE_GRUPOECONOMICO,
            HABITO.CHAVE_CLIENTE

        ORDER BY
            PRIORIDADE,
            CONDICAO,
            ORC_EM_ABERTO DESC
    """

    sql = sql.format(filtro_nao_carteira=filtro_nao_carteira, periodo=periodo)

    resultado = executar_oracle(sql, exportar_cabecalho=True, carteira=carteira)

    if not resultado:
        return []

    return resultado


def eventos_em_aberto_por_dia(carteira: str = '%%') -> list | None:
    """Retorna eventos do dia e em atraso"""
    carteira, filtro_nao_carteira = carteira_mapping(carteira)

    sql = """
        SELECT
            CLIENTES_HISTORICO.DATA,
            TO_CHAR(CLIENTES_HISTORICO.DATA, 'DY') AS DIA,
            VENDEDORES.NOMERED AS CARTEIRA,
            V_COLABORADORES.USUARIO,
            COUNT(DISTINCT CLIENTES_HISTORICO.CHAVE) AS EVENTOS

        FROM
            COPLAS.V_COLABORADORES,
            COPLAS.CLIENTES_HISTORICO,
            COPLAS.CLIENTES,
            COPLAS.VENDEDORES

        WHERE
            CLIENTES.CODCLI = CLIENTES_HISTORICO.CHAVE_CLIENTE
            AND CLIENTES_HISTORICO.CHAVE_RESPONSAVEL = V_COLABORADORES.CHAVE
            AND CLIENTES.CHAVE_VENDEDOR3 = VENDEDORES.CODVENDEDOR
            AND CLIENTES_HISTORICO.DATA_REALIZADO IS NULL

            AND VENDEDORES.NOMERED LIKE :carteira
            AND {filtro_nao_carteira}
            1 = 1

        GROUP BY
            CLIENTES_HISTORICO.DATA,
            VENDEDORES.NOMERED,
            V_COLABORADORES.USUARIO

        ORDER BY
            CLIENTES_HISTORICO.DATA DESC
    """

    sql = sql.format(filtro_nao_carteira=filtro_nao_carteira)

    resultado = executar_oracle(sql, exportar_cabecalho=True, carteira=carteira)

    if not resultado:
        return []

    return resultado


def map_relatorio_vendas_sql_string_placeholders(fonte: Literal['orcamentos', 'pedidos', 'faturamentos'], trocar_para_itens_excluidos: bool = False, **kwargs_formulario):
    """
        SQLs estão em um dict onde a chave é o nome do campo do formulario e o valor é um dict com o placeholder como
        chave e o codigo sql como valor
    """
    coluna_mes_a_mes = kwargs_formulario.get('coluna_mes_a_mes', False)
    if coluna_mes_a_mes:
        mes_a_mes_inicio = pd.date_range(kwargs_formulario['inicio'], kwargs_formulario['fim'], freq='MS')
        mes_a_mes_fim = pd.date_range(kwargs_formulario['inicio'], kwargs_formulario['fim'], freq='ME')
        mes_a_mes = list(zip(mes_a_mes_inicio.date, mes_a_mes_fim.date))

    familia_produto = kwargs_formulario.get('familia_produto', False)
    chave_familia_produto = '= :chave_familia_produto'
    if isinstance(familia_produto, list):
        chave_familia_produto = ', '.join(f'{f}' for f in familia_produto)
        chave_familia_produto = f'IN ({chave_familia_produto})'

    incluir_orcamentos_oportunidade = kwargs_formulario.pop('incluir_orcamentos_oportunidade', False)
    incluir_orcamentos_oportunidade = "" if incluir_orcamentos_oportunidade else "ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO' AND"

    incluir_sem_valor_comercial = kwargs_formulario.pop('incluir_sem_valor_comercial', False)
    if fonte == 'orcamentos':
        incluir_sem_valor_comercial = "" if incluir_sem_valor_comercial else "ORCAMENTOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND"
    if fonte == 'pedidos':
        incluir_sem_valor_comercial = "" if incluir_sem_valor_comercial else "PEDIDOS.CHAVE_TIPO IN (SELECT CHAVE FROM COPLAS.PEDIDOS_TIPOS WHERE VALOR_COMERCIAL = 'SIM') AND"
    if fonte == 'faturamentos':
        incluir_sem_valor_comercial = "" if incluir_sem_valor_comercial else "NOTAS.VALOR_COMERCIAL = 'SIM' AND"

    conversao_moeda = ""
    if fonte == 'orcamentos':
        conversao_moeda = " * CASE WHEN ORCAMENTOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT COALESCE(MAX(VALOR), 1) FROM COPLAS.VALORES WHERE CODMOEDA = ORCAMENTOS.CHAVE_MOEDA AND DATA = ORCAMENTOS.DATA_PEDIDO) END"
    if fonte == 'pedidos':
        conversao_moeda = " * CASE WHEN PEDIDOS.CHAVE_MOEDA = 0 THEN 1 ELSE (SELECT COALESCE(MAX(VALOR), 1) FROM COPLAS.VALORES WHERE CODMOEDA = PEDIDOS.CHAVE_MOEDA AND DATA = PEDIDOS.DATA_PEDIDO) END"

    nao_converter_moeda = kwargs_formulario.pop('nao_converter_moeda', False)
    if nao_converter_moeda:
        conversao_moeda = ""

    notas_proximo_evento_grupo_economico_from = """
        (
            SELECT CLIENTES.CHAVE_GRUPOECONOMICO,
                MIN(CLIENTES_HISTORICO.DATA) AS PROXIMO_EVENTO_GRUPO,
                MAX(CLIENTES_HISTORICO.DATA) AS ULTIMO_EVENTO_GRUPO
            FROM COPLAS.CLIENTES,
                COPLAS.CLIENTES_HISTORICO
            WHERE CLIENTES.CODCLI = CLIENTES_HISTORICO.CHAVE_CLIENTE
                AND CLIENTES_HISTORICO.DATA_REALIZADO IS NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO IS NOT NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO != 1
            GROUP BY CLIENTES.CHAVE_GRUPOECONOMICO
        ) PROXIMO_EVENTO_GRUPO,
    """
    notas_proximo_evento_grupo_economico_join = "CLIENTES.CHAVE_GRUPOECONOMICO = PROXIMO_EVENTO_GRUPO.CHAVE_GRUPOECONOMICO(+) AND"

    notas_documentos_from = """
        (
            SELECT DISTINCT
                NOTAS.CHAVE AS CHAVE_NOTA,
                ORCAMENTOS.NUMPED AS ORCAMENTO,
                PEDIDOS.NUMPED AS PEDIDO,
                ORCAMENTOS.LOG_NOME_INCLUSAO AS LOG_INCLUSAO_ORCAMENTO

            FROM
                COPLAS.ORCAMENTOS,
                COPLAS.PEDIDOS,
                COPLAS.NOTAS_ITENS,
                COPLAS.NOTAS

            WHERE
                NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
                PEDIDOS.CHAVE = NOTAS_ITENS.NUMPED AND
                ORCAMENTOS.CHAVE = PEDIDOS.CHAVE_ORCAMENTO AND

                NOTAS.DATA_EMISSAO >= :data_inicio AND
                NOTAS.DATA_EMISSAO <= :data_fim
        ) DOCUMENTOS,
    """
    notas_documentos_join = "NOTAS.CHAVE = DOCUMENTOS.CHAVE_NOTA(+) AND"

    notas_transportadoras_from = "COPLAS.TRANSPORTADORAS,"
    notas_transportadoras_join = "TRANSPORTADORAS.CODTRANSP = NOTAS.CHAVE_TRANSPORTADORA AND"

    notas_destino_from = """
        (
            SELECT
                NOTAS_ORDEM.CHAVE AS CHAVE_NOTA,
                ESTADOS_ORDEM.SIGLA AS UF_ORDEM,
                CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM

            FROM
                COPLAS.ESTADOS ESTADOS_ORDEM,
                COPLAS.NOTAS NOTAS_ORDEM,
                COPLAS.CLIENTES CLIENTES_ORDEM

            WHERE
                NOTAS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND
                CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE
        ) UF_ORDEM,
        COPLAS.ESTADOS ESTADOS_PLATAFORMAS,
        COPLAS.PLATAFORMAS,
    """
    notas_destino_join = """
        NOTAS.CHAVE = UF_ORDEM.CHAVE_NOTA(+) AND
        PLATAFORMAS.UF_ENT = ESTADOS_PLATAFORMAS.CHAVE(+) AND
        NOTAS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
    """

    notas_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    notas_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE), 0), 2) AS MC_VALOR"
    notas_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR

        , ROUND(COALESCE(
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN NOTAS_ITENS.VALOR_MERCADORIAS - (NOTAS_ITENS.PESO_LIQUIDO / NOTAS_PESO_LIQUIDO.PESO_LIQUIDO * NOTAS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        , 0), 2) AS MC_VALOR_COR
    """
    notas_lfrete_aliquotas_itens_coluna = "LFRETE.ALIQUOTA_PIS, LFRETE.ALIQUOTA_COFINS, LFRETE.ALIQUOTA_ICMS, LFRETE.ALIQUOTA_IR, LFRETE.ALIQUOTA_CSLL, LFRETE.ALIQUOTA_COMISSAO, LFRETE.ALIQUOTA_DESPESA_ADM, LFRETE.ALIQUOTA_DESPESA_COM, LFRETE.ALIQUOTAS_TOTAIS,"

    notas_lfrete_from = """
        (
            SELECT
                CHAVE_NOTA_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA IN (7767, 12441) THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ,
                MAX(ALIQUOTA_PIS) AS ALIQUOTA_PIS,
                MAX(ALIQUOTA_COFINS) AS ALIQUOTA_COFINS,
                MAX(ALIQUOTA_ICMS) AS ALIQUOTA_ICMS,
                MAX(ALIQUOTA_IR) AS ALIQUOTA_IR,
                MAX(ALIQUOTA_CSLL) AS ALIQUOTA_CSLL,
                MAX(ALIQUOTA_COMISSAO) AS ALIQUOTA_COMISSAO,
                MAX(ALIQUOTA_DESPESA_ADM) AS ALIQUOTA_DESPESA_ADM,
                MAX(ALIQUOTA_DESPESA_COM) AS ALIQUOTA_DESPESA_COM,
                MAX(ALIQUOTA_PIS + ALIQUOTA_COFINS + ALIQUOTA_ICMS + ALIQUOTA_IR + ALIQUOTA_CSLL + ALIQUOTA_COMISSAO + ALIQUOTA_DESPESA_ADM + ALIQUOTA_DESPESA_COM) AS ALIQUOTAS_TOTAIS

            FROM
                (
                    {lfrete_notas} AND

                        {incluir_sem_valor_comercial}
                        NOTAS.DATA_EMISSAO >= :data_inicio AND
                        NOTAS.DATA_EMISSAO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_NOTA_ITEM
        ) LFRETE,
    """.format(lfrete_notas=lfrete_notas, incluir_sem_valor_comercial=incluir_sem_valor_comercial)
    notas_lfrete_join = "LFRETE.CHAVE_NOTA_ITEM = NOTAS_ITENS.CHAVE AND"

    notas_valor_mercadorias = "NOTAS_ITENS.VALOR_MERCADORIAS - (COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO, 0) * NOTAS.VALOR_FRETE_INCL_ITEM, 0))"

    notas_valor_mercadorias_mes_a_mes = ""
    if fonte == 'faturamentos' and coluna_mes_a_mes:
        for i, f in mes_a_mes:
            notas_valor_mercadorias_mes_a_mes += f", SUM(CASE WHEN NOTAS.DATA_EMISSAO >= TO_DATE('{i}', 'YYYY-MM-DD') AND NOTAS.DATA_EMISSAO <= TO_DATE('{f}', 'YYYY-MM-DD') THEN {notas_valor_mercadorias} ELSE 0 END) AS VALOR_{i.year}_{i.month:02d}"

    map_sql_notas_base = {
        'valor_mercadorias': f"SUM({notas_valor_mercadorias}) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': """
            (
                SELECT
                    NOTAS_ITENS.CHAVE_NOTA,
                    SUM(NOTAS_ITENS.PESO_LIQUIDO) AS PESO_LIQUIDO

                FROM
                    COPLAS.NOTAS_ITENS

                GROUP BY
                    NOTAS_ITENS.CHAVE_NOTA
            ) NOTAS_PESO_LIQUIDO,
        """,

        'fonte_itens': "COPLAS.NOTAS_ITENS,",

        'fonte': "COPLAS.NOTAS,",

        'fonte_joins': """
            PRODUTOS.CPROD = NOTAS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
            NOTAS.CHAVE = NOTAS_PESO_LIQUIDO.CHAVE_NOTA(+) AND
            NOTAS.CHAVE_JOB = JOBS.CODIGO AND
        """,

        'fonte_where': "{incluir_sem_valor_comercial}".format(incluir_sem_valor_comercial=incluir_sem_valor_comercial),

        'fonte_where_data': """
            NOTAS.DATA_EMISSAO >= :data_inicio AND
            NOTAS.DATA_EMISSAO <= :data_fim
        """,
    }

    map_sql_notas = {
        'data_vencimento_titulo_entre': {'data_vencimento_titulo_entre_pesquisa': "EXISTS(SELECT RECEBER.CHAVE FROM COPLAS.RECEBER WHERE NOTAS.CHAVE = RECEBER.CHAVE_NOTA AND RECEBER.DATAVENCIMENTO BETWEEN :data_vencimento_titulo_inicio AND :data_vencimento_titulo_fim) AND", },

        'coluna_parcelas': {'parcelas_campo_alias': "NOTAS.PARCELAS,",
                            'parcelas_campo': "NOTAS.PARCELAS,", },

        # coluna_custo_materia_prima_notas Não funciona com a fluxus, conferir se mudar a forma de beneficiamento
        'coluna_custo_materia_prima_notas': {'custo_materia_prima_notas_campo_alias': "SUM(COALESCE(CASE WHEN PRODUTOS.CHAVE_MARCA IN (178, 177) THEN NOTAS_ITENS.CUSTO_MP_MED * NOTAS_ITENS.QUANTIDADE ELSE NULL END, CASE WHEN PRODUTOS.CHAVE_MARCA NOT IN (178, 177) THEN NOTAS_ITENS.ANALISE_CUSTO_MEDIO - NOTAS_ITENS.CUSTO_MP_MED * NOTAS_ITENS.QUANTIDADE ELSE NULL END, 0)) AS CUSTO_MP,"},

        'cfop_baixa_estoque': {'cfop_baixa_estoque_pesquisa': "NOTAS_ITENS.CHAVE_NATUREZA IN (SELECT CHAVE FROM COPLAS.NATUREZA WHERE BAIXA_ESTOQUE = 'SIM' AND CHAVE NOT IN (8791, 10077)) AND", },

        'coluna_dias_decorridos': {'dias_decorridos_campo_alias': "COUNT(DISTINCT TRUNC(NOTAS.DATA_EMISSAO)) AS DIAS_DECORRIDOS,"},

        'coluna_estoque_abc': {'estoque_abc_campo_alias': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END AS ESTOQUE_ABC,",
                               'estoque_abc_campo': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END,", },
        'estoque_abc': {'estoque_abc_pesquisa': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END = UPPER(:estoque_abc) AND", },

        'coluna_cgc': {'cgc_campo_alias': "CLIENTES.CGC,",
                       'cgc_campo': "CLIENTES.CGC,", },

        'coluna_inscricao_estadual': {'inscricao_estadual_campo_alias': "CLIENTES.INSCRICAO AS INSCRICAO_ESTADUAL,",
                                      'inscricao_estadual_campo': "CLIENTES.INSCRICAO,", },

        'coluna_mes_a_mes': {'mes_a_mes_campo_alias': notas_valor_mercadorias_mes_a_mes},

        'coluna_peso_bruto_nota': {'peso_bruto_nota_campo_alias': "NOTAS.PESO_BRUTO AS PESO_BRUTO_NOTA,",
                                   'peso_bruto_nota_campo': "NOTAS.PESO_BRUTO,", },

        'coluna_custo_total_item': {'custo_total_item_campo_alias': "SUM(NOTAS_ITENS.ANALISE_CUSTO_MEDIO) AS CUSTO_TOTAL_ITEM,"},

        'coluna_valor_bruto': {'valor_bruto_campo_alias': "SUM(NOTAS_ITENS.VALOR_CONTABIL) AS VALOR_BRUTO,"},

        'coluna_frete_incluso_item': {'frete_incluso_item_campo_alias': "SUM(COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO, 0) * NOTAS.VALOR_FRETE_INCL_ITEM, 0)) AS FRETE_INCLUSO_ITEM,"},
        'coluna_frete_destacado': {'frete_destacado_campo_alias': "SUM(NOTAS_ITENS.RATEIO_FRETE) AS FRETE_DESTACADO,"},

        'coluna_cobranca_frete': {'cobranca_frete_campo_alias': "CASE WHEN NOTAS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN NOTAS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END AS COBRANCA_FRETE,",
                                  'cobranca_frete_campo': "CASE WHEN NOTAS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN NOTAS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END,", },
        'cobranca_frete_cif': {'cobranca_frete_cif_pesquisa': "(NOTAS.CHAVE_TRANSPORTADORA = 8475 OR NOTAS.COBRANCA_FRETE IN (0, 1, 4, 5)) AND", },

        'valor_mercadorias_maior_igual': {'having': 'HAVING 1=1',
                                          'valor_mercadorias_maior_igual_having': "AND SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO, 0) * NOTAS.VALOR_FRETE_INCL_ITEM, 0))) >= :valor_mercadorias_maior_igual", },

        'coluna_media_dia': {'media_dia_campo_alias': "SUM(NOTAS_ITENS.VALOR_MERCADORIAS - (COALESCE(NOTAS_ITENS.PESO_LIQUIDO / NULLIF(NOTAS_PESO_LIQUIDO.PESO_LIQUIDO, 0) * NOTAS.VALOR_FRETE_INCL_ITEM, 0))) / COUNT(DISTINCT NOTAS.DATA_EMISSAO) AS MEDIA_DIA,", },

        'coluna_data_emissao': {'data_emissao_campo_alias': "NOTAS.DATA_EMISSAO,",
                                'data_emissao_campo': "NOTAS.DATA_EMISSAO,", },
        'data_emissao_menor_que': {'data_emissao_menor_que_pesquisa': "NOTAS.DATA_EMISSAO < :data_emissao_menor_que AND", },

        'coluna_data_despacho': {'data_despacho_campo_alias': "NOTAS.DATA_DESPACHO,",
                                 'data_despacho_campo': "NOTAS.DATA_DESPACHO,", },
        'data_despacho_maior_igual': {'data_despacho_maior_igual_pesquisa': "NOTAS.DATA_DESPACHO >= :data_despacho_maior_igual AND", },
        'data_despacho_menor_igual': {'data_despacho_menor_igual_pesquisa': "NOTAS.DATA_DESPACHO <= :data_despacho_menor_igual AND", },

        'coluna_data_saida': {'data_saida_campo_alias': "NOTAS.DATA_SAIDA,",
                              'data_saida_campo': "NOTAS.DATA_SAIDA,", },

        'coluna_quantidade_volumes': {'quantidade_volumes_campo_alias': "NOTAS.VOLUMES_QUANTIDADE,",
                                      'quantidade_volumes_campo': "NOTAS.VOLUMES_QUANTIDADE,", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM NOTAS.DATA_EMISSAO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM NOTAS.DATA_EMISSAO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

        'coluna_representante': {'representante_campo_alias': "REPRESENTANTES.NOMERED AS REPRESENTANTE,",
                                 'representante_campo': "REPRESENTANTES.NOMERED,",
                                 'representantes_from': "COPLAS.VENDEDORES REPRESENTANTES,",
                                 'representantes_join': "CLIENTES.CODVEND = REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_representante_documento': {'representante_documento_campo_alias': "REPRESENTANTES_DOCUMENTO.NOMERED AS REPRESENTANTE_DOCUMENTO,",
                                           'representante_documento_campo': "REPRESENTANTES_DOCUMENTO.NOMERED,",
                                           'representantes_documento_from': "COPLAS.VENDEDORES REPRESENTANTES_DOCUMENTO,",
                                           'representantes_documento_join': "NOTAS.CHAVE_VENDEDOR = REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante': {'segundo_representante_campo_alias': "SEGUNDO_REPRESENTANTES.NOMERED AS SEGUNDO_REPRESENTANTE,",
                                         'segundo_representante_campo': "SEGUNDO_REPRESENTANTES.NOMERED,",
                                         'segundo_representantes_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES,",
                                         'segundo_representantes_join': "CLIENTES.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante_documento': {'segundo_representante_documento_campo_alias': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED AS SEGUNDO_REPRESENTANTE_DOCUMENTO,",
                                                   'segundo_representante_documento_campo': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED,",
                                                   'segundo_representantes_documento_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES_DOCUMENTO,",
                                                   'segundo_representantes_documento_join': "NOTAS.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_tipo_cliente': {'tipo_cliente_campo_alias': "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,",
                                'tipo_cliente_campo': "CLIENTES_TIPOS.DESCRICAO,", },
        'tipo_cliente': {'tipo_cliente_pesquisa': "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND", },

        'coluna_familia_produto': {'familia_produto_campo_alias': "FAMILIA_PRODUTOS.FAMILIA AS FAMILIA_PRODUTO,",
                                   'familia_produto_campo': "FAMILIA_PRODUTOS.FAMILIA,", },
        'familia_produto': {'familia_produto_pesquisa': "FAMILIA_PRODUTOS.CHAVE {chave_familia_produto} AND".format(chave_familia_produto=chave_familia_produto), },

        'coluna_chave_produto': {'chave_produto_campo_alias': "PRODUTOS.CPROD AS CHAVE_PRODUTO,",
                                 'chave_produto_campo': "PRODUTOS.CPROD,", },
        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },
        'produto_marca': {'produto_marca_pesquisa': "PRODUTOS.CHAVE_MARCA = :chave_produto_marca AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(NOTAS_ITENS.PRECO_TABELA) AS PRECO_TABELA_INCLUSAO,", },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(NOTAS_ITENS.PRECO_FATURADO), 2) AS PRECO_VENDA_MEDIO,", },

        'coluna_preco_venda': {'preco_venda_campo_alias': "ROUND(NOTAS_ITENS.PRECO_FATURADO, 2) AS PRECO_VENDA,", },

        'coluna_desconto': {'desconto_campo_alias': "ROUND((1 - (NOTAS_ITENS.PRECO_FATURADO / NOTAS_ITENS.PRECO_TABELA)) * 100, 2) AS DESCONTO,",
                            'desconto_campo': "ROUND((1 - (NOTAS_ITENS.PRECO_FATURADO / NOTAS_ITENS.PRECO_TABELA)) * 100, 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(NOTAS_ITENS.QUANTIDADE) AS QUANTIDADE,", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'coluna_estado_origem': {'estado_origem_campo_alias': "JOBS.UF AS UF_ORIGEM,",
                                 'estado_origem_campo': "JOBS.UF,", },

        'coluna_estado_destino': {'estado_destino_campo_alias': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA) AS UF_DESTINO,",
                                  'estado_destino_campo': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA),",
                                  'destino_from': notas_destino_from,
                                  'destino_join': notas_destino_join, },
        'coluna_cidade_destino': {'cidade_destino_campo_alias': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE) AS CIDADE_DESTINO,",
                                  'cidade_destino_campo': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE),",
                                  'destino_from': notas_destino_from,
                                  'destino_join': notas_destino_join, },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': """
            CLIENTES.STATUS != 'X' AND
            NOT EXISTS(
                SELECT DISTINCT
                    CLIENTES.CHAVE_GRUPOECONOMICO

                FROM
                    COPLAS.CLIENTES,
                    COPLAS.NOTAS

                WHERE
                    CLIENTES.CHAVE_GRUPOECONOMICO = GRUPO_ECONOMICO.CHAVE AND
                    CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
                    NOTAS.VALOR_COMERCIAL = 'SIM' AND

                    NOTAS.DATA_EMISSAO > :data_fim
            ) AND
            NOT EXISTS(
                SELECT DISTINCT
                    ORCAMENTOS.CHAVE_CLIENTE

                FROM
                    COPLAS.ORCAMENTOS

                WHERE
                    ORCAMENTOS.CHAVE_CLIENTE = CLIENTES.CODCLI AND
                    ORCAMENTOS.STATUS = 'EM ABERTO' AND
                    ORCAMENTOS.REGISTRO_OPORTUNIDADE = 'NAO'
            ) AND
        """, },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "", },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'ordenar_valor_descrescente_prioritario': {'ordenar_valor_descrescente_prioritario': "VALOR_MERCADORIAS DESC,", },

        'ordenar_sequencia_prioritario': {'sequencia_campo': "NOTAS_ITENS.CHAVE,",
                                          'ordenar_sequencia_prioritario': "NOTAS_ITENS.CHAVE,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT NOTAS.NF) AS QUANTIDADE_DOCUMENTOS,", },
        'quantidade_documentos_maior_que': {'having': 'HAVING 1=1',
                                            'quantidade_documentos_maior_que_having': "AND COUNT(DISTINCT NOTAS.NF) > :quantidade_documentos_maior_que", },

        'coluna_quantidade_meses': {'quantidade_meses_campo_alias': "COUNT(DISTINCT TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM')) AS QUANTIDADE_MESES,", },
        'quantidade_meses_maior_que': {'having': 'HAVING 1=1',
                                       'quantidade_meses_maior_que_having': "AND COUNT(DISTINCT TO_CHAR(NOTAS.DATA_EMISSAO, 'YYYY-MM')) > :quantidade_meses_maior_que", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "",
                                            'status_produto_orcamento_campo': "", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "",
                                                 'status_produto_orcamento_tipo_campo': "",
                                                 'status_produto_orcamento_tipo_from': "",
                                                 'status_produto_orcamento_tipo_join': "", },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "",
                                          'status_produto_orcamento_tipo_from': "",
                                          'status_produto_orcamento_tipo_join': "", },

        'coluna_rentabilidade': {'lfrete_coluna': notas_lfrete_coluna,
                                 'lfrete_valor_coluna': notas_lfrete_valor_coluna,
                                 'lfrete_from': notas_lfrete_from,
                                 'lfrete_join': notas_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': notas_lfrete_coluna,
                                       'lfrete_valor_coluna': notas_lfrete_valor_coluna,
                                       'lfrete_from': notas_lfrete_from,
                                       'lfrete_join': notas_lfrete_join, },
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': notas_lfrete_cor_coluna,
                                     'lfrete_from': notas_lfrete_from,
                                     'lfrete_join': notas_lfrete_join, },
        'coluna_aliquotas_itens': {'lfrete_coluna_aliquotas_itens': notas_lfrete_aliquotas_itens_coluna,
                                   'lfrete_from': notas_lfrete_from,
                                   'lfrete_join': notas_lfrete_join, },
        'coluna_mc_cor_ajuste': {'mc_cor_ajuste_campo_alias': ", CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END AS MC_COR_AJUSTE",
                                 'mc_cor_ajuste_campo': "CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END,", },

        'coluna_pis': {'pis_campo_alias': "SUM(NOTAS_ITENS.ANALISE_PIS) AS PIS,", },
        'coluna_cofins': {'cofins_campo_alias': "SUM(NOTAS_ITENS.ANALISE_COFINS) AS COFINS,", },
        'coluna_icms': {'icms_campo_alias': "SUM(NOTAS_ITENS.ANALISE_ICMS) AS ICMS,", },
        'coluna_icms_partilha': {'icms_partilha_campo_alias': "SUM(NOTAS_ITENS.ANALISE_ICMS_PARTILHA) AS ICMS_PARTILHA,", },
        'coluna_ipi': {'ipi_campo_alias': "SUM(NOTAS_ITENS.VALOR_IPI_COM_FRETE) AS IPI,", },
        'coluna_st': {'st_campo_alias': "SUM(NOTAS_ITENS.ICMS_SUBSTITUICAO_VALOR) AS ST,", },
        'coluna_irpj_csll': {'irpj_csll_campo_alias': "SUM(NOTAS_ITENS.ANALISE_CONTRIBUICAO) AS IRPJ_CSLL,", },

        'coluna_documento': {'documento_campo_alias': "NOTAS.NF AS DOCUMENTO,",
                             'documento_campo': "NOTAS.NF,", },
        'coluna_chave_documento': {'chave_documento_campo_alias': "NOTAS.CHAVE AS CHAVE_DOCUMENTO,",
                                   'chave_documento_campo': "NOTAS.CHAVE,", },
        'documento': {'documento_pesquisa': "NOTAS.NF = :documento AND", },

        'coluna_log_nome_inclusao_documento': {'log_nome_inclusao_documento_campo_alias': "NOTAS.LOG_NOME_FATURAMENTO AS LOG_NOME_INCLUSAO_DOCUMENTO,",
                                               'log_nome_inclusao_documento_campo': "NOTAS.LOG_NOME_FATURAMENTO,", },

        'coluna_orcamento': {'orcamento_campo_alias': "DOCUMENTOS.ORCAMENTO,",
                             'orcamento_campo': "DOCUMENTOS.ORCAMENTO,",
                             'documentos_from': notas_documentos_from,
                             'documentos_join': notas_documentos_join, },
        'coluna_pedido': {'pedido_campo_alias': "DOCUMENTOS.PEDIDO,",
                          'pedido_campo': "DOCUMENTOS.PEDIDO,",
                          'documentos_from': notas_documentos_from,
                          'documentos_join': notas_documentos_join, },
        'coluna_nota': {'nota_campo_alias': "",
                        'nota_campo': "",
                        'documentos_from': "",
                        'documentos_join': "", },
        'coluna_log_nome_inclusao_orcamento': {'log_nome_inclusao_orcamento_campo_alias': "DOCUMENTOS.LOG_INCLUSAO_ORCAMENTO,",
                                               'log_nome_inclusao_orcamento_campo': "DOCUMENTOS.LOG_INCLUSAO_ORCAMENTO,",
                                               'documentos_from': notas_documentos_from,
                                               'documentos_join': notas_documentos_join, },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "",
                                      'data_entrega_itens_campo': "", },
        'data_entrega_itens_maior_que': {'data_entrega_itens_maior_que_pesquisa': "", },
        'data_entrega_itens_menor_igual': {'data_entrega_itens_menor_igual_pesquisa': "", },

        'coluna_status_documento': {'status_documento_campo_alias': "CASE NOTAS.ATIVA WHEN 'NAO' THEN 'CANCELADA' END AS STATUS_DOCUMENTO,",
                                    'status_documento_campo': "CASE NOTAS.ATIVA WHEN 'NAO' THEN 'CANCELADA' END,", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "",
                                          'orcamento_oportunidade_campo': "", },

        'status_cliente_ativo': {'status_cliente_ativo_pesquisa': "CLIENTES.STATUS IN ('Y', 'P') AND", },

        'informacao_estrategica': {'informacao_estrategica_pesquisa': "EXISTS(SELECT CLIENTES_INFORMACOES_CLI.CHAVE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES.CODCLI = CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE AND CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO = :chave_informacao_estrategica) AND", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'coluna_peso_produto_proprio': {'peso_produto_proprio_campo_alias': "SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN NOTAS_ITENS.PESO_LIQUIDO ELSE 0 END) AS PESO_PP,", },

        'coluna_especie': {'especie_campo_alias': "CASE NOTAS.ESPECIE WHEN 'S' THEN 'SAIDA' WHEN 'E' THEN 'ENTRADA' END AS ESPECIE,",
                           'especie_campo': "CASE NOTAS.ESPECIE WHEN 'S' THEN 'SAIDA' WHEN 'E' THEN 'ENTRADA' END,", },
        'especie': {'especie_pesquisa': "NOTAS.ESPECIE = :especie AND", },

        'coluna_chave_transportadora': {'chave_transportadora_campo_alias': "NOTAS.CHAVE_TRANSPORTADORA AS CHAVE_TRANSPORTADORA,",
                                        'chave_transportadora_campo': "NOTAS.CHAVE_TRANSPORTADORA,", },
        'coluna_transportadora': {'transportadora_campo_alias': "TRANSPORTADORAS.NOMERED AS TRANSPORTADORA,",
                                  'transportadora_campo': "TRANSPORTADORAS.NOMERED,",
                                  'transportadoras_from': notas_transportadoras_from,
                                  'transportadoras_join': notas_transportadoras_join, },
        'transportadoras_geram_titulos': {'transportadoras_geram_titulos_pesquisa': "TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND",
                                          'transportadoras_from': notas_transportadoras_from,
                                          'transportadoras_join': notas_transportadoras_join, },

        'coluna_proximo_evento_grupo_economico': {'proximo_evento_grupo_economico_campo_alias': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_campo': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_from': notas_proximo_evento_grupo_economico_from,
                                                  'proximo_evento_grupo_economico_join': notas_proximo_evento_grupo_economico_join, },
        'desconsiderar_grupo_economico_com_evento_futuro': {'desconsiderar_grupo_economico_com_evento_futuro_pesquisa': "(PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO IS NULL OR PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO <= TRUNC(SYSDATE)) AND",
                                                            'proximo_evento_grupo_economico_from': notas_proximo_evento_grupo_economico_from,
                                                            'proximo_evento_grupo_economico_join': notas_proximo_evento_grupo_economico_join, },

        'coluna_destino_mercadorias': {'destino_mercadorias_campo_alias': "NOTAS.DESTINO AS DESTINO_MERCADORIAS,",
                                       'destino_mercadorias_campo': "NOTAS.DESTINO,", },

        'coluna_zona_franca_alc': {'zona_franca_alc_campo_alias': "CASE WHEN NOTAS.ZONA_FRANCA = 'SIM' OR NOTAS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END AS ZONA_FRANCA_ALC,",
                                   'zona_franca_alc_campo': "CASE WHEN NOTAS.ZONA_FRANCA = 'SIM' OR NOTAS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END,", },
    }

    pedidos_proximo_evento_grupo_economico_from = """
        (
            SELECT CLIENTES.CHAVE_GRUPOECONOMICO,
                MIN(CLIENTES_HISTORICO.DATA) AS PROXIMO_EVENTO_GRUPO,
                MAX(CLIENTES_HISTORICO.DATA) AS ULTIMO_EVENTO_GRUPO
            FROM COPLAS.CLIENTES,
                COPLAS.CLIENTES_HISTORICO
            WHERE CLIENTES.CODCLI = CLIENTES_HISTORICO.CHAVE_CLIENTE
                AND CLIENTES_HISTORICO.DATA_REALIZADO IS NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO IS NOT NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO != 1
            GROUP BY CLIENTES.CHAVE_GRUPOECONOMICO
        ) PROXIMO_EVENTO_GRUPO,
    """
    pedidos_proximo_evento_grupo_economico_join = "CLIENTES.CHAVE_GRUPOECONOMICO = PROXIMO_EVENTO_GRUPO.CHAVE_GRUPOECONOMICO(+) AND"

    pedidos_documentos_from = """
        (
            SELECT DISTINCT
                PEDIDOS.CHAVE AS CHAVE_PEDIDO,
                ORCAMENTOS.NUMPED AS ORCAMENTO,
                NOTAS.NF AS NOTA,
                ORCAMENTOS.LOG_NOME_INCLUSAO AS LOG_INCLUSAO_ORCAMENTO

            FROM
                COPLAS.ORCAMENTOS,
                COPLAS.PEDIDOS,
                COPLAS.NOTAS_ITENS,
                COPLAS.NOTAS

            WHERE
                ORCAMENTOS.CHAVE = PEDIDOS.CHAVE_ORCAMENTO AND
                PEDIDOS.CHAVE = NOTAS_ITENS.NUMPED(+) AND
                NOTAS.CHAVE(+) = NOTAS_ITENS.CHAVE_NOTA AND

                (
                    (
                        NOTAS.FATURA_REMESSA_ORDEM IS NULL AND
                        NOTAS.ESPECIE = 'S' AND
                        (
                            NOTAS.TIPO_TRIANGULARIZACAO = 'FATURA' OR
                            NOTAS.TIPO_TRIANGULARIZACAO IS NULL
                        )
                    ) OR
                    NOTAS.CHAVE IS NULL
                ) AND

                PEDIDOS.DATA_PEDIDO >= :data_inicio AND
                PEDIDOS.DATA_PEDIDO <= :data_fim
        ) DOCUMENTOS,
    """
    pedidos_documentos_join = "PEDIDOS.CHAVE = DOCUMENTOS.CHAVE_PEDIDO(+) AND"

    pedidos_transportadoras_from = "COPLAS.TRANSPORTADORAS,"
    pedidos_transportadoras_join = "TRANSPORTADORAS.CODTRANSP = PEDIDOS.CHAVE_TRANSPORTADORA AND"

    pedidos_destino_from = """
        (
            SELECT
                PEDIDOS_ORDEM.CHAVE AS CHAVE_PEDIDO,
                ESTADOS_ORDEM.SIGLA AS UF_ORDEM,
                CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM

            FROM
                COPLAS.ESTADOS ESTADOS_ORDEM,
                COPLAS.PEDIDOS PEDIDOS_ORDEM,
                COPLAS.CLIENTES CLIENTES_ORDEM

            WHERE
                PEDIDOS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND
                CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE
        ) UF_ORDEM,
        COPLAS.ESTADOS ESTADOS_PLATAFORMAS,
        COPLAS.PLATAFORMAS,
    """
    pedidos_destino_join = """
        PEDIDOS.CHAVE = UF_ORDEM.CHAVE_PEDIDO(+) AND
        PLATAFORMAS.UF_ENT = ESTADOS_PLATAFORMAS.CHAVE(+) AND
        PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
    """

    pedidos_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    pedidos_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE {conversao_moeda}), 0), 2) AS MC_VALOR".format(
        conversao_moeda=conversao_moeda)
    pedidos_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR

        , ROUND(COALESCE(
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN PEDIDOS_ITENS.VALOR_TOTAL - (PEDIDOS_ITENS.PESO_LIQUIDO / PEDIDOS.PESO_LIQUIDO * PEDIDOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        , 0), 2) AS MC_VALOR_COR
    """.format(conversao_moeda=conversao_moeda)
    pedidos_lfrete_aliquotas_itens_coluna = "LFRETE.ALIQUOTA_PIS, LFRETE.ALIQUOTA_COFINS, LFRETE.ALIQUOTA_ICMS, LFRETE.ALIQUOTA_IR, LFRETE.ALIQUOTA_CSLL, LFRETE.ALIQUOTA_COMISSAO, LFRETE.ALIQUOTA_DESPESA_ADM, LFRETE.ALIQUOTA_DESPESA_COM, LFRETE.ALIQUOTAS_TOTAIS,"
    pedidos_lfrete_from = """
        (
            SELECT
                CHAVE_PEDIDO_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA IN (7767, 12441) THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ,
                MAX(ALIQUOTA_PIS) AS ALIQUOTA_PIS,
                MAX(ALIQUOTA_COFINS) AS ALIQUOTA_COFINS,
                MAX(ALIQUOTA_ICMS) AS ALIQUOTA_ICMS,
                MAX(ALIQUOTA_IR) AS ALIQUOTA_IR,
                MAX(ALIQUOTA_CSLL) AS ALIQUOTA_CSLL,
                MAX(ALIQUOTA_COMISSAO) AS ALIQUOTA_COMISSAO,
                MAX(ALIQUOTA_DESPESA_ADM) AS ALIQUOTA_DESPESA_ADM,
                MAX(ALIQUOTA_DESPESA_COM) AS ALIQUOTA_DESPESA_COM,
                MAX(ALIQUOTA_PIS + ALIQUOTA_COFINS + ALIQUOTA_ICMS + ALIQUOTA_IR + ALIQUOTA_CSLL + ALIQUOTA_COMISSAO + ALIQUOTA_DESPESA_ADM + ALIQUOTA_DESPESA_COM) AS ALIQUOTAS_TOTAIS

            FROM
                (
                    {lfrete_pedidos} AND

                        {incluir_sem_valor_comercial}
                        PEDIDOS.DATA_PEDIDO >= :data_inicio AND
                        PEDIDOS.DATA_PEDIDO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_PEDIDO_ITEM
        ) LFRETE,
    """.format(lfrete_pedidos=lfrete_pedidos, incluir_sem_valor_comercial=incluir_sem_valor_comercial)
    pedidos_lfrete_join = "LFRETE.CHAVE_PEDIDO_ITEM = PEDIDOS_ITENS.CHAVE AND"

    pedidos_valor_mercadorias = "(PEDIDOS_ITENS.VALOR_TOTAL - (COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO, 0) * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}".format(
        conversao_moeda=conversao_moeda)

    pedidos_valor_mercadorias_mes_a_mes = ""
    if fonte == 'pedidos' and coluna_mes_a_mes:
        for i, f in mes_a_mes:
            pedidos_valor_mercadorias_mes_a_mes += f", SUM(CASE WHEN PEDIDOS.DATA_PEDIDO >= TO_DATE('{i}', 'YYYY-MM-DD') AND PEDIDOS.DATA_PEDIDO <= TO_DATE('{f}', 'YYYY-MM-DD') THEN {pedidos_valor_mercadorias} ELSE 0 END) AS VALOR_{i.year}_{i.month:02d}"

    map_sql_pedidos_base = {
        'valor_mercadorias': f"SUM({pedidos_valor_mercadorias}) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': "",

        'fonte_itens': "COPLAS.PEDIDOS_ITENS,",

        'fonte': "COPLAS.PEDIDOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = PEDIDOS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
            PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO AND
            PEDIDOS.CHAVE_JOB = JOBS.CODIGO AND
        """,

        'fonte_where': "{incluir_sem_valor_comercial}".format(incluir_sem_valor_comercial=incluir_sem_valor_comercial),

        'fonte_where_data': """
            PEDIDOS.DATA_PEDIDO >= :data_inicio AND
            PEDIDOS.DATA_PEDIDO <= :data_fim
        """,
    }

    map_sql_pedidos = {
        'data_vencimento_titulo_entre': {'data_vencimento_titulo_entre_pesquisa': "", },

        'coluna_parcelas': {'parcelas_campo_alias': "",
                            'parcelas_campo': "", },

        # coluna_custo_materia_prima_notas Não funciona com a fluxus, conferir se mudar a forma de beneficiamento
        'coluna_custo_materia_prima_notas': {'custo_materia_prima_notas_campo_alias': ""},

        'cfop_baixa_estoque': {'cfop_baixa_estoque_pesquisa': "PEDIDOS_ITENS.CHAVE_NATUREZA IN (SELECT CHAVE FROM COPLAS.NATUREZA WHERE BAIXA_ESTOQUE = 'SIM' AND CHAVE NOT IN (8791, 10077)) AND", },

        'coluna_dias_decorridos': {'dias_decorridos_campo_alias': "COUNT(DISTINCT TRUNC(PEDIDOS.DATA_PEDIDO)) AS DIAS_DECORRIDOS,"},

        'coluna_estoque_abc': {'estoque_abc_campo_alias': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END AS ESTOQUE_ABC,",
                               'estoque_abc_campo': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END,", },
        'estoque_abc': {'estoque_abc_pesquisa': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END = UPPER(:estoque_abc) AND", },

        'coluna_cgc': {'cgc_campo_alias': "CLIENTES.CGC,",
                       'cgc_campo': "CLIENTES.CGC,", },

        'coluna_inscricao_estadual': {'inscricao_estadual_campo_alias': "CLIENTES.INSCRICAO AS INSCRICAO_ESTADUAL,",
                                      'inscricao_estadual_campo': "CLIENTES.INSCRICAO,", },

        'coluna_mes_a_mes': {'mes_a_mes_campo_alias': pedidos_valor_mercadorias_mes_a_mes},

        'coluna_peso_bruto_nota': {'peso_bruto_nota_campo_alias': "",
                                   'peso_bruto_nota_campo': "", },

        'coluna_custo_total_item': {'custo_total_item_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_CUSTO_MEDIO {conversao_moeda}) AS CUSTO_TOTAL_ITEM,".format(conversao_moeda=conversao_moeda)},

        'coluna_valor_bruto': {'valor_bruto_campo_alias': "SUM((PEDIDOS_ITENS.VALOR_TOTAL + PEDIDOS_ITENS.RATEIO_FRETE + PEDIDOS_ITENS.VALOR_IPI + PEDIDOS_ITENS.ICMS_SUBSTITUICAO_VALOR) {conversao_moeda}) AS VALOR_BRUTO,".format(conversao_moeda=conversao_moeda)},

        'coluna_frete_incluso_item': {'frete_incluso_item_campo_alias': "SUM((COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO, 0) * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0)) {conversao_moeda}) AS FRETE_INCLUSO_ITEM,".format(conversao_moeda=conversao_moeda)},
        'coluna_frete_destacado': {'frete_destacado_campo_alias': "SUM(PEDIDOS_ITENS.RATEIO_FRETE {conversao_moeda}) AS FRETE_DESTACADO,".format(conversao_moeda=conversao_moeda)},

        'coluna_cobranca_frete': {'cobranca_frete_campo_alias': "CASE WHEN PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN PEDIDOS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END AS COBRANCA_FRETE,",
                                  'cobranca_frete_campo': "CASE WHEN PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN PEDIDOS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END,", },
        'cobranca_frete_cif': {'cobranca_frete_cif_pesquisa': "(PEDIDOS.CHAVE_TRANSPORTADORA = 8475 OR PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5)) AND", },

        'valor_mercadorias_maior_igual': {'having': 'HAVING 1=1',
                                          'valor_mercadorias_maior_igual_having': "AND SUM((PEDIDOS_ITENS.VALOR_TOTAL - (COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO, 0) * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}) >= :valor_mercadorias_maior_igual".format(conversao_moeda=conversao_moeda), },

        'coluna_media_dia': {'media_dia_campo_alias': "SUM((PEDIDOS_ITENS.VALOR_TOTAL - (COALESCE(PEDIDOS_ITENS.PESO_LIQUIDO / NULLIF(PEDIDOS.PESO_LIQUIDO, 0) * PEDIDOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}) / COUNT(DISTINCT PEDIDOS.DATA_PEDIDO) AS MEDIA_DIA,".format(conversao_moeda=conversao_moeda)},

        'coluna_data_emissao': {'data_emissao_campo_alias': "PEDIDOS.DATA_PEDIDO AS DATA_EMISSAO,",
                                'data_emissao_campo': "PEDIDOS.DATA_PEDIDO,", },
        'data_emissao_menor_que': {'data_emissao_menor_que_pesquisa': "PEDIDOS.DATA_PEDIDO < :data_emissao_menor_que AND", },

        'coluna_data_despacho': {'data_despacho_campo_alias': "",
                                 'data_despacho_campo': "", },
        'data_despacho_maior_igual': {'data_despacho_maior_igual_pesquisa': "", },
        'data_despacho_menor_igual': {'data_despacho_menor_igual_pesquisa': "", },

        'coluna_data_saida': {'data_saida_campo_alias': "",
                              'data_saida_campo': "", },

        'coluna_quantidade_volumes': {'quantidade_volumes_campo_alias': "",
                                      'quantidade_volumes_campo': "", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM PEDIDOS.DATA_PEDIDO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM PEDIDOS.DATA_PEDIDO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM PEDIDOS.DATA_PEDIDO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM PEDIDOS.DATA_PEDIDO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

        'coluna_representante': {'representante_campo_alias': "REPRESENTANTES.NOMERED AS REPRESENTANTE,",
                                 'representante_campo': "REPRESENTANTES.NOMERED,",
                                 'representantes_from': "COPLAS.VENDEDORES REPRESENTANTES,",
                                 'representantes_join': "CLIENTES.CODVEND = REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_representante_documento': {'representante_documento_campo_alias': "REPRESENTANTES_DOCUMENTO.NOMERED AS REPRESENTANTE_DOCUMENTO,",
                                           'representante_documento_campo': "REPRESENTANTES_DOCUMENTO.NOMERED,",
                                           'representantes_documento_from': "COPLAS.VENDEDORES REPRESENTANTES_DOCUMENTO,",
                                           'representantes_documento_join': "PEDIDOS.CHAVE_VENDEDOR = REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante': {'segundo_representante_campo_alias': "SEGUNDO_REPRESENTANTES.NOMERED AS SEGUNDO_REPRESENTANTE,",
                                         'segundo_representante_campo': "SEGUNDO_REPRESENTANTES.NOMERED,",
                                         'segundo_representantes_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES,",
                                         'segundo_representantes_join': "CLIENTES.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante_documento': {'segundo_representante_documento_campo_alias': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED AS SEGUNDO_REPRESENTANTE_DOCUMENTO,",
                                                   'segundo_representante_documento_campo': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED,",
                                                   'segundo_representantes_documento_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES_DOCUMENTO,",
                                                   'segundo_representantes_documento_join': "PEDIDOS.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_tipo_cliente': {'tipo_cliente_campo_alias': "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,",
                                'tipo_cliente_campo': "CLIENTES_TIPOS.DESCRICAO,", },
        'tipo_cliente': {'tipo_cliente_pesquisa': "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND", },

        'coluna_familia_produto': {'familia_produto_campo_alias': "FAMILIA_PRODUTOS.FAMILIA AS FAMILIA_PRODUTO,",
                                   'familia_produto_campo': "FAMILIA_PRODUTOS.FAMILIA,", },
        'familia_produto': {'familia_produto_pesquisa': "FAMILIA_PRODUTOS.CHAVE {chave_familia_produto} AND".format(chave_familia_produto=chave_familia_produto), },

        'coluna_chave_produto': {'chave_produto_campo_alias': "PRODUTOS.CPROD AS CHAVE_PRODUTO,",
                                 'chave_produto_campo': "PRODUTOS.CPROD,", },
        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },
        'produto_marca': {'produto_marca_pesquisa': "PRODUTOS.CHAVE_MARCA = :chave_marca AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(PEDIDOS_ITENS.PRECO_TABELA {conversao_moeda}) AS PRECO_TABELA_INCLUSAO,".format(conversao_moeda=conversao_moeda), },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(PEDIDOS_ITENS.PRECO_VENDA {conversao_moeda}), 2) AS PRECO_VENDA_MEDIO,".format(conversao_moeda=conversao_moeda), },

        'coluna_preco_venda': {'preco_venda_campo_alias': "ROUND(MAX(PEDIDOS_ITENS.PRECO_VENDA {conversao_moeda}), 2) AS PRECO_VENDA,".format(conversao_moeda=conversao_moeda), },

        'coluna_desconto': {'desconto_campo_alias': "ROUND((1 - (PEDIDOS_ITENS.PRECO_VENDA / PEDIDOS_ITENS.PRECO_TABELA)) * 100, 2) AS DESCONTO,",
                            'desconto_campo': "ROUND((1 - (PEDIDOS_ITENS.PRECO_VENDA / PEDIDOS_ITENS.PRECO_TABELA)) * 100, 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(PEDIDOS_ITENS.QUANTIDADE) AS QUANTIDADE,", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'coluna_estado_origem': {'estado_origem_campo_alias': "JOBS.UF AS UF_ORIGEM,",
                                 'estado_origem_campo': "JOBS.UF,", },

        'coluna_estado_destino': {'estado_destino_campo_alias': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA) AS UF_DESTINO,",
                                  'estado_destino_campo': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA),",
                                  'destino_from': pedidos_destino_from,
                                  'destino_join': pedidos_destino_join, },
        'coluna_cidade_destino': {'cidade_destino_campo_alias': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE) AS CIDADE_DESTINO,",
                                  'cidade_destino_campo': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE),",
                                  'destino_from': pedidos_destino_from,
                                  'destino_join': pedidos_destino_join, },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': "", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "", },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'ordenar_valor_descrescente_prioritario': {'ordenar_valor_descrescente_prioritario': "VALOR_MERCADORIAS DESC,", },

        'ordenar_sequencia_prioritario': {'sequencia_campo': "PEDIDOS_ITENS.CHAVE,",
                                          'ordenar_sequencia_prioritario': "PEDIDOS_ITENS.CHAVE,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT PEDIDOS.NUMPED) AS QUANTIDADE_DOCUMENTOS,", },
        'quantidade_documentos_maior_que': {'having': 'HAVING 1=1',
                                            'quantidade_documentos_maior_que_having': "AND COUNT(DISTINCT PEDIDOS.NUMPED) > :quantidade_documentos_maior_que", },

        'coluna_quantidade_meses': {'quantidade_meses_campo_alias': "COUNT(DISTINCT TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM')) AS QUANTIDADE_MESES,", },
        'quantidade_meses_maior_que': {'having': 'HAVING 1=1',
                                       'quantidade_meses_maior_que_having': "AND COUNT(DISTINCT TO_CHAR(PEDIDOS.DATA_PEDIDO, 'YYYY-MM')) > :quantidade_meses_maior_que", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "",
                                            'status_produto_orcamento_campo': "", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "",
                                                 'status_produto_orcamento_tipo_campo': "",
                                                 'status_produto_orcamento_tipo_from': "",
                                                 'status_produto_orcamento_tipo_join': "", },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "",
                                          'status_produto_orcamento_tipo_from': "",
                                          'status_produto_orcamento_tipo_join': "", },

        'coluna_rentabilidade': {'lfrete_coluna': pedidos_lfrete_coluna,
                                 'lfrete_valor_coluna': pedidos_lfrete_valor_coluna,
                                 'lfrete_from': pedidos_lfrete_from,
                                 'lfrete_join': pedidos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': pedidos_lfrete_coluna,
                                       'lfrete_valor_coluna': pedidos_lfrete_valor_coluna,
                                       'lfrete_from': pedidos_lfrete_from,
                                       'lfrete_join': pedidos_lfrete_join, },
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': pedidos_lfrete_cor_coluna,
                                     'lfrete_from': pedidos_lfrete_from,
                                     'lfrete_join': pedidos_lfrete_join, },
        'coluna_aliquotas_itens': {'lfrete_coluna_aliquotas_itens': pedidos_lfrete_aliquotas_itens_coluna,
                                   'lfrete_from': pedidos_lfrete_from,
                                   'lfrete_join': pedidos_lfrete_join, },
        'coluna_mc_cor_ajuste': {'mc_cor_ajuste_campo_alias': ", CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END AS MC_COR_AJUSTE",
                                 'mc_cor_ajuste_campo': "CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END,", },

        'coluna_pis': {'pis_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_PIS {conversao_moeda}) AS PIS,".format(conversao_moeda=conversao_moeda), },
        'coluna_cofins': {'cofins_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_COFINS {conversao_moeda}) AS COFINS,".format(conversao_moeda=conversao_moeda), },
        'coluna_icms': {'icms_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_ICMS {conversao_moeda}) AS ICMS,".format(conversao_moeda=conversao_moeda), },
        'coluna_icms_partilha': {'icms_partilha_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_ICMS_PARTILHA {conversao_moeda}) AS ICMS_PARTILHA,".format(conversao_moeda=conversao_moeda), },
        'coluna_ipi': {'ipi_campo_alias': "SUM(PEDIDOS_ITENS.VALOR_IPI {conversao_moeda}) AS IPI,".format(conversao_moeda=conversao_moeda), },
        'coluna_st': {'st_campo_alias': "SUM(PEDIDOS_ITENS.ICMS_SUBSTITUICAO_VALOR {conversao_moeda}) AS ST,".format(conversao_moeda=conversao_moeda), },
        'coluna_irpj_csll': {'irpj_csll_campo_alias': "SUM(PEDIDOS_ITENS.ANALISE_CONTRIBUICAO {conversao_moeda}) AS IRPJ_CSLL,".format(conversao_moeda=conversao_moeda), },

        'coluna_documento': {'documento_campo_alias': "PEDIDOS.NUMPED AS DOCUMENTO,",
                             'documento_campo': "PEDIDOS.NUMPED,", },
        'coluna_chave_documento': {'chave_documento_campo_alias': "PEDIDOS.CHAVE AS CHAVE_DOCUMENTO,",
                                   'chave_documento_campo': "PEDIDOS.CHAVE,", },
        'documento': {'documento_pesquisa': "PEDIDOS.NUMPED = :documento AND", },

        'coluna_log_nome_inclusao_documento': {'log_nome_inclusao_documento_campo_alias': "PEDIDOS.LOG_NOME AS LOG_NOME_INCLUSAO_DOCUMENTO,",
                                               'log_nome_inclusao_documento_campo': "PEDIDOS.LOG_NOME,", },

        'coluna_orcamento': {'orcamento_campo_alias': "DOCUMENTOS.ORCAMENTO,",
                             'orcamento_campo': "DOCUMENTOS.ORCAMENTO,",
                             'documentos_from': pedidos_documentos_from,
                             'documentos_join': pedidos_documentos_join, },
        'coluna_pedido': {'pedido_campo_alias': "",
                          'pedido_campo': "",
                          'documentos_from': "",
                          'documentos_join': "", },
        'coluna_nota': {'nota_campo_alias': "DOCUMENTOS.NOTA,",
                        'nota_campo': "DOCUMENTOS.NOTA,",
                        'documentos_from': pedidos_documentos_from,
                        'documentos_join': pedidos_documentos_join, },
        'coluna_log_nome_inclusao_orcamento': {'log_nome_inclusao_orcamento_campo_alias': "DOCUMENTOS.LOG_INCLUSAO_ORCAMENTO,",
                                               'log_nome_inclusao_orcamento_campo': "DOCUMENTOS.LOG_INCLUSAO_ORCAMENTO,",
                                               'documentos_from': pedidos_documentos_from,
                                               'documentos_join': pedidos_documentos_join, },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "PEDIDOS_ITENS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "PEDIDOS_ITENS.DATA_ENTREGA,", },
        'data_entrega_itens_maior_que': {'data_entrega_itens_maior_que_pesquisa': "PEDIDOS_ITENS.DATA_ENTREGA > :data_entrega_itens_maior_que AND", },
        'data_entrega_itens_menor_igual': {'data_entrega_itens_menor_igual_pesquisa': "PEDIDOS_ITENS.DATA_ENTREGA <= :data_entrega_itens_menor_igual AND", },

        'coluna_status_documento': {'status_documento_campo_alias': "PEDIDOS.STATUS AS STATUS_DOCUMENTO,",
                                    'status_documento_campo': "PEDIDOS.STATUS,", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "PEDIDOS.STATUS IN ('EM ABERTO', 'BLOQUEADO') AND", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "",
                                          'orcamento_oportunidade_campo': "", },

        'status_cliente_ativo': {'status_cliente_ativo_pesquisa': "CLIENTES.STATUS IN ('Y', 'P') AND", },

        'informacao_estrategica': {'informacao_estrategica_pesquisa': "EXISTS(SELECT CLIENTES_INFORMACOES_CLI.CHAVE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES.CODCLI = CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE AND CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO = :chave_informacao_estrategica) AND", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'coluna_peso_produto_proprio': {'peso_produto_proprio_campo_alias': "SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN PEDIDOS_ITENS.PESO_LIQUIDO ELSE 0 END) AS PESO_PP,", },

        'coluna_especie': {'especie_campo_alias': "",
                           'especie_campo': "", },
        'especie': {'especie_pesquisa': "", },

        'coluna_chave_transportadora': {'chave_transportadora_campo_alias': "PEDIDOS.CHAVE_TRANSPORTADORA AS CHAVE_TRANSPORTADORA,",
                                        'chave_transportadora_campo': "PEDIDOS.CHAVE_TRANSPORTADORA,", },
        'coluna_transportadora': {'transportadora_campo_alias': "TRANSPORTADORAS.NOMERED AS TRANSPORTADORA,",
                                  'transportadora_campo': "TRANSPORTADORAS.NOMERED,",
                                  'transportadoras_from': pedidos_transportadoras_from,
                                  'transportadoras_join': pedidos_transportadoras_join, },
        'transportadoras_geram_titulos': {'transportadoras_geram_titulos_pesquisa': "TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND",
                                          'transportadoras_from': pedidos_transportadoras_from,
                                          'transportadoras_join': pedidos_transportadoras_join, },

        'coluna_proximo_evento_grupo_economico': {'proximo_evento_grupo_economico_campo_alias': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_campo': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_from': pedidos_proximo_evento_grupo_economico_from,
                                                  'proximo_evento_grupo_economico_join': pedidos_proximo_evento_grupo_economico_join, },
        'desconsiderar_grupo_economico_com_evento_futuro': {'desconsiderar_grupo_economico_com_evento_futuro_pesquisa': "(PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO IS NULL OR PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO <= TRUNC(SYSDATE)) AND",
                                                            'proximo_evento_grupo_economico_from': pedidos_proximo_evento_grupo_economico_from,
                                                            'proximo_evento_grupo_economico_join': pedidos_proximo_evento_grupo_economico_join, },

        'coluna_destino_mercadorias': {'destino_mercadorias_campo_alias': "PEDIDOS.DESTINO AS DESTINO_MERCADORIAS,",
                                       'destino_mercadorias_campo': "PEDIDOS.DESTINO,", },

        'coluna_zona_franca_alc': {'zona_franca_alc_campo_alias': "CASE WHEN PEDIDOS.ZONA_FRANCA = 'SIM' OR PEDIDOS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END AS ZONA_FRANCA_ALC,",
                                   'zona_franca_alc_campo': "CASE WHEN PEDIDOS.ZONA_FRANCA = 'SIM' OR PEDIDOS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END,", },
    }

    orcamentos_proximo_evento_grupo_economico_from = """
        (
            SELECT CLIENTES.CHAVE_GRUPOECONOMICO,
                MIN(CLIENTES_HISTORICO.DATA) AS PROXIMO_EVENTO_GRUPO,
                MAX(CLIENTES_HISTORICO.DATA) AS ULTIMO_EVENTO_GRUPO
            FROM COPLAS.CLIENTES,
                COPLAS.CLIENTES_HISTORICO
            WHERE CLIENTES.CODCLI = CLIENTES_HISTORICO.CHAVE_CLIENTE
                AND CLIENTES_HISTORICO.DATA_REALIZADO IS NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO IS NOT NULL
                AND CLIENTES.CHAVE_GRUPOECONOMICO != 1
            GROUP BY CLIENTES.CHAVE_GRUPOECONOMICO
        ) PROXIMO_EVENTO_GRUPO,
    """
    orcamentos_proximo_evento_grupo_economico_join = "CLIENTES.CHAVE_GRUPOECONOMICO = PROXIMO_EVENTO_GRUPO.CHAVE_GRUPOECONOMICO(+) AND"

    orcamentos_documentos_from = """
        (
            SELECT DISTINCT
                ORCAMENTOS.CHAVE AS CHAVE_ORCAMENTO,
                PEDIDOS.NUMPED AS PEDIDO,
                NOTAS.NF AS NOTA

            FROM
                COPLAS.ORCAMENTOS,
                COPLAS.PEDIDOS,
                COPLAS.NOTAS_ITENS,
                COPLAS.NOTAS

            WHERE
                ORCAMENTOS.CHAVE = PEDIDOS.CHAVE_ORCAMENTO(+) AND
                PEDIDOS.CHAVE = NOTAS_ITENS.NUMPED(+) AND
                NOTAS.CHAVE(+) = NOTAS_ITENS.CHAVE_NOTA AND

                (
                    (
                        NOTAS.FATURA_REMESSA_ORDEM IS NULL AND
                        NOTAS.ESPECIE = 'S' AND
                        (
                            NOTAS.TIPO_TRIANGULARIZACAO = 'FATURA' OR
                            NOTAS.TIPO_TRIANGULARIZACAO IS NULL
                        )
                    ) OR
                    NOTAS.CHAVE IS NULL
                ) AND

                ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
                ORCAMENTOS.DATA_PEDIDO <= :data_fim
        ) DOCUMENTOS,
    """
    orcamentos_documentos_join = "ORCAMENTOS.CHAVE = DOCUMENTOS.CHAVE_ORCAMENTO(+) AND"

    orcamentos_transportadoras_from = "COPLAS.TRANSPORTADORAS,"
    orcamentos_transportadoras_join = "TRANSPORTADORAS.CODTRANSP = ORCAMENTOS.CHAVE_TRANSPORTADORA AND"

    orcamentos_status_produto_orcamento_tipo_from = "COPLAS.STATUS_ORCAMENTOS_ITENS,"
    orcamentos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS.STATUS AND"

    orcamentos_destino_from = """
        (
            SELECT
                ORCAMENTOS_ORDEM.CHAVE AS CHAVE_ORCAMENTO,
                ESTADOS_ORDEM.SIGLA AS UF_ORDEM,
                CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM

            FROM
                COPLAS.ESTADOS ESTADOS_ORDEM,
                COPLAS.ORCAMENTOS ORCAMENTOS_ORDEM,
                COPLAS.CLIENTES CLIENTES_ORDEM

            WHERE
                ORCAMENTOS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND
                CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE
        ) UF_ORDEM,
        COPLAS.ESTADOS ESTADOS_PLATAFORMAS,
        COPLAS.PLATAFORMAS,
    """
    orcamentos_destino_join = """
        ORCAMENTOS.CHAVE = UF_ORDEM.CHAVE_ORCAMENTO(+) AND
        PLATAFORMAS.UF_ENT = ESTADOS_PLATAFORMAS.CHAVE(+) AND
        ORCAMENTOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
    """

    orcamentos_lfrete_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE) / NULLIF(SUM(ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)), 0), 0) * 100, 2) AS MC"
    orcamentos_lfrete_valor_coluna = ", ROUND(COALESCE(SUM(LFRETE.MC_SEM_FRETE {conversao_moeda}), 0), 2) AS MC_VALOR".format(
        conversao_moeda=conversao_moeda)
    orcamentos_lfrete_cor_coluna = """
        , ROUND(COALESCE(
        (
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END), 0), 0)
        ) / NULLIF(SUM(ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM)), 0)
        , 0) * 100, 2) AS MC_COR

        , ROUND(COALESCE(
        (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PP {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) - 0.01) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PT {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        + (COALESCE(SUM(LFRETE.MC_SEM_FRETE_PQ {conversao_moeda}) / NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0) + 0.04) * COALESCE(NULLIF(SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN ORCAMENTOS_ITENS.VALOR_TOTAL - (ORCAMENTOS_ITENS.PESO_LIQUIDO / ORCAMENTOS.PESO_LIQUIDO * ORCAMENTOS.VALOR_FRETE_INCL_ITEM) ELSE 0 END {conversao_moeda}), 0), 0)
        , 0), 2) AS MC_VALOR_COR
    """.format(conversao_moeda=conversao_moeda)
    orcamentos_lfrete_aliquotas_itens_coluna = "LFRETE.ALIQUOTA_PIS, LFRETE.ALIQUOTA_COFINS, LFRETE.ALIQUOTA_ICMS, LFRETE.ALIQUOTA_IR, LFRETE.ALIQUOTA_CSLL, LFRETE.ALIQUOTA_COMISSAO, LFRETE.ALIQUOTA_DESPESA_ADM, LFRETE.ALIQUOTA_DESPESA_COM, LFRETE.ALIQUOTAS_TOTAIS,"
    orcamentos_lfrete_from = """
        (
            SELECT
                CHAVE_ORCAMENTO_ITEM,
                ROUND(SUM(MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM), 2) AS MC_SEM_FRETE,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 7766 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PP,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA IN (7767, 12441) THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PT,
                ROUND(SUM(CASE WHEN CHAVE_FAMILIA = 8378 THEN MC + PIS + COFINS + ICMS + IR + CSLL + COMISSAO_FRETE_ITEM + DESPESA_ADM_FRETE_ITEM + DESPESA_COM_FRETE_ITEM ELSE 0 END), 2) AS MC_SEM_FRETE_PQ,
                MAX(ALIQUOTA_PIS) AS ALIQUOTA_PIS,
                MAX(ALIQUOTA_COFINS) AS ALIQUOTA_COFINS,
                MAX(ALIQUOTA_ICMS) AS ALIQUOTA_ICMS,
                MAX(ALIQUOTA_IR) AS ALIQUOTA_IR,
                MAX(ALIQUOTA_CSLL) AS ALIQUOTA_CSLL,
                MAX(ALIQUOTA_COMISSAO) AS ALIQUOTA_COMISSAO,
                MAX(ALIQUOTA_DESPESA_ADM) AS ALIQUOTA_DESPESA_ADM,
                MAX(ALIQUOTA_DESPESA_COM) AS ALIQUOTA_DESPESA_COM,
                MAX(ALIQUOTA_PIS + ALIQUOTA_COFINS + ALIQUOTA_ICMS + ALIQUOTA_IR + ALIQUOTA_CSLL + ALIQUOTA_COMISSAO + ALIQUOTA_DESPESA_ADM + ALIQUOTA_DESPESA_COM) AS ALIQUOTAS_TOTAIS

            FROM
                (
                    {lfrete_orcamentos} AND

                        {incluir_sem_valor_comercial}
                        {incluir_orcamentos_oportunidade}
                        ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
                        ORCAMENTOS.DATA_PEDIDO <= :data_fim
                ) LFRETE

            GROUP BY
                CHAVE_ORCAMENTO_ITEM
        ) LFRETE,
    """.format(lfrete_orcamentos=lfrete_orcamentos, incluir_orcamentos_oportunidade=incluir_orcamentos_oportunidade,
               incluir_sem_valor_comercial=incluir_sem_valor_comercial)
    orcamentos_lfrete_join = "LFRETE.CHAVE_ORCAMENTO_ITEM = ORCAMENTOS_ITENS.CHAVE AND"

    orcamentos_valor_mercadorias = "(ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO, 0) * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}".format(
        conversao_moeda=conversao_moeda)

    orcamentos_valor_mercadorias_mes_a_mes = ""
    if fonte == 'orcamentos' and coluna_mes_a_mes:
        for i, f in mes_a_mes:
            orcamentos_valor_mercadorias_mes_a_mes += f", SUM(CASE WHEN ORCAMENTOS.DATA_PEDIDO >= TO_DATE('{i}', 'YYYY-MM-DD') AND ORCAMENTOS.DATA_PEDIDO <= TO_DATE('{f}', 'YYYY-MM-DD') THEN {orcamentos_valor_mercadorias} ELSE 0 END) AS VALOR_{i.year}_{i.month:02d}"

    map_sql_orcamentos_base = {
        'valor_mercadorias': f"SUM({orcamentos_valor_mercadorias}) AS VALOR_MERCADORIAS",

        'notas_peso_liquido_from': "",

        'fonte_itens': "COPLAS.ORCAMENTOS_ITENS,",

        'fonte': "COPLAS.ORCAMENTOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = ORCAMENTOS_ITENS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND
            ORCAMENTOS.CHAVE_JOB = JOBS.CODIGO AND
        """,

        'fonte_where': """
            {incluir_sem_valor_comercial}
            {incluir_orcamentos_oportunidade}
            ORCAMENTOS.NUMPED != 204565 AND
        """.format(incluir_orcamentos_oportunidade=incluir_orcamentos_oportunidade,
                   incluir_sem_valor_comercial=incluir_sem_valor_comercial),

        'fonte_where_data': """
            ORCAMENTOS.DATA_PEDIDO >= :data_inicio AND
            ORCAMENTOS.DATA_PEDIDO <= :data_fim
        """,
    }

    map_sql_orcamentos = {
        'data_vencimento_titulo_entre': {'data_vencimento_titulo_entre_pesquisa': "", },

        'coluna_parcelas': {'parcelas_campo_alias': "",
                            'parcelas_campo': "", },

        # coluna_custo_materia_prima_notas Não funciona com a fluxus, conferir se mudar a forma de beneficiamento
        'coluna_custo_materia_prima_notas': {'custo_materia_prima_notas_campo_alias': ""},

        'cfop_baixa_estoque': {'cfop_baixa_estoque_pesquisa': "ORCAMENTOS_ITENS.CHAVE_NATUREZA IN (SELECT CHAVE FROM COPLAS.NATUREZA WHERE BAIXA_ESTOQUE = 'SIM' AND CHAVE NOT IN (8791, 10077)) AND", },

        'coluna_dias_decorridos': {'dias_decorridos_campo_alias': "COUNT(DISTINCT TRUNC(ORCAMENTOS.DATA_PEDIDO)) AS DIAS_DECORRIDOS,"},

        'coluna_estoque_abc': {'estoque_abc_campo_alias': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END AS ESTOQUE_ABC,",
                               'estoque_abc_campo': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END,", },
        'estoque_abc': {'estoque_abc_pesquisa': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END = UPPER(:estoque_abc) AND", },

        'coluna_cgc': {'cgc_campo_alias': "CLIENTES.CGC,",
                       'cgc_campo': "CLIENTES.CGC,", },

        'coluna_inscricao_estadual': {'inscricao_estadual_campo_alias': "CLIENTES.INSCRICAO AS INSCRICAO_ESTADUAL,",
                                      'inscricao_estadual_campo': "CLIENTES.INSCRICAO,", },

        'coluna_mes_a_mes': {'mes_a_mes_campo_alias': orcamentos_valor_mercadorias_mes_a_mes},

        'coluna_peso_bruto_nota': {'peso_bruto_nota_campo_alias': "",
                                   'peso_bruto_nota_campo': "", },

        'coluna_custo_total_item': {'custo_total_item_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_CUSTO_MEDIO {conversao_moeda}) AS CUSTO_TOTAL_ITEM,".format(conversao_moeda=conversao_moeda)},

        'coluna_valor_bruto': {'valor_bruto_campo_alias': "SUM((ORCAMENTOS_ITENS.VALOR_TOTAL + ORCAMENTOS_ITENS.RATEIO_FRETE + ORCAMENTOS_ITENS.VALOR_IPI + ORCAMENTOS_ITENS.ICMS_SUBSTITUICAO_VALOR) {conversao_moeda}) AS VALOR_BRUTO,".format(conversao_moeda=conversao_moeda)},

        'coluna_frete_incluso_item': {'frete_incluso_item_campo_alias': "SUM((COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO, 0) * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0)) {conversao_moeda}) AS FRETE_INCLUSO_ITEM,".format(conversao_moeda=conversao_moeda)},
        'coluna_frete_destacado': {'frete_destacado_campo_alias': "SUM(ORCAMENTOS_ITENS.RATEIO_FRETE {conversao_moeda}) AS FRETE_DESTACADO,".format(conversao_moeda=conversao_moeda)},

        'coluna_cobranca_frete': {'cobranca_frete_campo_alias': "CASE WHEN ORCAMENTOS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN ORCAMENTOS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END AS COBRANCA_FRETE,",
                                  'cobranca_frete_campo': "CASE WHEN ORCAMENTOS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN ORCAMENTOS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END,", },
        'cobranca_frete_cif': {'cobranca_frete_cif_pesquisa': "(ORCAMENTOS.CHAVE_TRANSPORTADORA = 8475 OR ORCAMENTOS.COBRANCA_FRETE IN (0, 1, 4, 5)) AND", },

        'valor_mercadorias_maior_igual': {'having': 'HAVING 1=1',
                                          'valor_mercadorias_maior_igual_having': "AND SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO, 0) * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}) >= :valor_mercadorias_maior_igual".format(conversao_moeda=conversao_moeda), },

        'coluna_media_dia': {'media_dia_campo_alias': "SUM((ORCAMENTOS_ITENS.VALOR_TOTAL - (COALESCE(ORCAMENTOS_ITENS.PESO_LIQUIDO / NULLIF(ORCAMENTOS.PESO_LIQUIDO, 0) * ORCAMENTOS.VALOR_FRETE_INCL_ITEM, 0))) {conversao_moeda}) / COUNT(DISTINCT ORCAMENTOS.DATA_PEDIDO) AS MEDIA_DIA,".format(conversao_moeda=conversao_moeda)},

        'coluna_data_emissao': {'data_emissao_campo_alias': "ORCAMENTOS.DATA_PEDIDO AS DATA_EMISSAO,",
                                'data_emissao_campo': "ORCAMENTOS.DATA_PEDIDO,", },
        'data_emissao_menor_que': {'data_emissao_menor_que_pesquisa': "ORCAMENTOS.DATA_PEDIDO < :data_emissao_menor_que AND", },

        'coluna_data_despacho': {'data_despacho_campo_alias': "",
                                 'data_despacho_campo': "", },
        'data_despacho_maior_igual': {'data_despacho_maior_igual_pesquisa': "", },
        'data_despacho_menor_igual': {'data_despacho_menor_igual_pesquisa': "", },

        'coluna_data_saida': {'data_saida_campo_alias': "",
                              'data_saida_campo': "", },

        'coluna_quantidade_volumes': {'quantidade_volumes_campo_alias': "",
                                      'quantidade_volumes_campo': "", },

        'coluna_ano_mes_emissao': {'ano_mes_emissao_campo_alias': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM') AS ANO_MES_EMISSAO,",
                                   'ano_mes_emissao_campo': "TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM'),", },

        'coluna_ano_emissao': {'ano_emissao_campo_alias': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO) AS ANO_EMISSAO,",
                               'ano_emissao_campo': "EXTRACT(YEAR FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_dia_emissao': {'dia_emissao_campo_alias': "EXTRACT(DAY FROM ORCAMENTOS.DATA_PEDIDO) AS DIA_EMISSAO,",
                               'dia_emissao_campo': "EXTRACT(DAY FROM ORCAMENTOS.DATA_PEDIDO),", },

        'coluna_grupo_economico': {'grupo_economico_campo_alias': "GRUPO_ECONOMICO.CHAVE AS CHAVE_GRUPO_ECONOMICO, GRUPO_ECONOMICO.DESCRICAO AS GRUPO,",
                                   'grupo_economico_campo': "GRUPO_ECONOMICO.CHAVE, GRUPO_ECONOMICO.DESCRICAO,", },
        'grupo_economico': {'grupo_economico_pesquisa': "UPPER(GRUPO_ECONOMICO.DESCRICAO) LIKE UPPER(:grupo_economico) AND", },

        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,", },
        'carteira': {'carteira_pesquisa': "VENDEDORES.CODVENDEDOR = :chave_carteira AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },

        'coluna_representante': {'representante_campo_alias': "REPRESENTANTES.NOMERED AS REPRESENTANTE,",
                                 'representante_campo': "REPRESENTANTES.NOMERED,",
                                 'representantes_from': "COPLAS.VENDEDORES REPRESENTANTES,",
                                 'representantes_join': "CLIENTES.CODVEND = REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_representante_documento': {'representante_documento_campo_alias': "REPRESENTANTES_DOCUMENTO.NOMERED AS REPRESENTANTE_DOCUMENTO,",
                                           'representante_documento_campo': "REPRESENTANTES_DOCUMENTO.NOMERED,",
                                           'representantes_documento_from': "COPLAS.VENDEDORES REPRESENTANTES_DOCUMENTO,",
                                           'representantes_documento_join': "ORCAMENTOS.CHAVE_VENDEDOR = REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante': {'segundo_representante_campo_alias': "SEGUNDO_REPRESENTANTES.NOMERED AS SEGUNDO_REPRESENTANTE,",
                                         'segundo_representante_campo': "SEGUNDO_REPRESENTANTES.NOMERED,",
                                         'segundo_representantes_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES,",
                                         'segundo_representantes_join': "CLIENTES.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES.CODVENDEDOR(+) AND", },

        'coluna_segundo_representante_documento': {'segundo_representante_documento_campo_alias': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED AS SEGUNDO_REPRESENTANTE_DOCUMENTO,",
                                                   'segundo_representante_documento_campo': "SEGUNDO_REPRESENTANTES_DOCUMENTO.NOMERED,",
                                                   'segundo_representantes_documento_from': "COPLAS.VENDEDORES SEGUNDO_REPRESENTANTES_DOCUMENTO,",
                                                   'segundo_representantes_documento_join': "ORCAMENTOS.CHAVE_VENDEDOR2 = SEGUNDO_REPRESENTANTES_DOCUMENTO.CODVENDEDOR(+) AND", },

        'coluna_tipo_cliente': {'tipo_cliente_campo_alias': "CLIENTES_TIPOS.DESCRICAO AS TIPO_CLIENTE,",
                                'tipo_cliente_campo': "CLIENTES_TIPOS.DESCRICAO,", },
        'tipo_cliente': {'tipo_cliente_pesquisa': "CLIENTES_TIPOS.CHAVE = :chave_tipo_cliente AND", },

        'coluna_familia_produto': {'familia_produto_campo_alias': "FAMILIA_PRODUTOS.FAMILIA AS FAMILIA_PRODUTO,",
                                   'familia_produto_campo': "FAMILIA_PRODUTOS.FAMILIA,", },
        'familia_produto': {'familia_produto_pesquisa': "FAMILIA_PRODUTOS.CHAVE {chave_familia_produto} AND".format(chave_familia_produto=chave_familia_produto), },

        'coluna_chave_produto': {'chave_produto_campo_alias': "PRODUTOS.CPROD AS CHAVE_PRODUTO,",
                                 'chave_produto_campo': "PRODUTOS.CPROD,", },
        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },
        'produto_marca': {'produto_marca_pesquisa': "PRODUTOS.CHAVE_MARCA = :chave_marca AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "MAX(ORCAMENTOS_ITENS.PRECO_TABELA {conversao_moeda}) AS PRECO_TABELA_INCLUSAO,".format(conversao_moeda=conversao_moeda), },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "ROUND(AVG(ORCAMENTOS_ITENS.PRECO_VENDA {conversao_moeda}), 2) AS PRECO_VENDA_MEDIO,".format(conversao_moeda=conversao_moeda), },

        'coluna_preco_venda': {'preco_venda_campo_alias': "ROUND(MAX(ORCAMENTOS_ITENS.PRECO_VENDA {conversao_moeda}), 2) AS PRECO_VENDA,".format(conversao_moeda=conversao_moeda), },

        'coluna_desconto': {'desconto_campo_alias': "ROUND((1 - (ORCAMENTOS_ITENS.PRECO_VENDA / ORCAMENTOS_ITENS.PRECO_TABELA)) * 100, 2) AS DESCONTO,",
                            'desconto_campo': "ROUND((1 - (ORCAMENTOS_ITENS.PRECO_VENDA / ORCAMENTOS_ITENS.PRECO_TABELA)) * 100, 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(ORCAMENTOS_ITENS.QUANTIDADE) AS QUANTIDADE,", },

        'coluna_cidade': {'cidade_campo_alias': "CLIENTES.CIDADE AS CIDADE_PRINCIPAL,",
                          'cidade_campo': "CLIENTES.CIDADE,", },
        'cidade': {'cidade_pesquisa': "UPPER(CLIENTES.CIDADE) LIKE UPPER(:cidade) AND", },

        'coluna_estado': {'estado_campo_alias': "ESTADOS.SIGLA AS UF_PRINCIPAL,",
                          'estado_campo': "ESTADOS.SIGLA,", },
        'estado': {'estado_pesquisa': "ESTADOS.CHAVE = :chave_estado AND", },

        'coluna_estado_origem': {'estado_origem_campo_alias': "JOBS.UF AS UF_ORIGEM,",
                                 'estado_origem_campo': "JOBS.UF,", },

        'coluna_estado_destino': {'estado_destino_campo_alias': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA) AS UF_DESTINO,",
                                  'estado_destino_campo': "COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS_PLATAFORMAS.SIGLA, ESTADOS.SIGLA),",
                                  'destino_from': orcamentos_destino_from,
                                  'destino_join': orcamentos_destino_join, },
        'coluna_cidade_destino': {'cidade_destino_campo_alias': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE) AS CIDADE_DESTINO,",
                                  'cidade_destino_campo': "COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE),",
                                  'destino_from': orcamentos_destino_from,
                                  'destino_join': orcamentos_destino_join, },

        'nao_compraram_depois': {'nao_compraram_depois_pesquisa': "", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "{} AND".format(justificativas(False)), },

        'coluna_proporcao': {'proporcao_campo': "VALOR_MERCADORIAS DESC,", },

        'ordenar_valor_descrescente_prioritario': {'ordenar_valor_descrescente_prioritario': "VALOR_MERCADORIAS DESC,", },

        'ordenar_sequencia_prioritario': {'sequencia_campo': "ORCAMENTOS_ITENS.ORDEM,",
                                          'ordenar_sequencia_prioritario': "ORCAMENTOS_ITENS.ORDEM,", },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "COUNT(DISTINCT ORCAMENTOS.NUMPED) AS QUANTIDADE_DOCUMENTOS,", },
        'quantidade_documentos_maior_que': {'having': 'HAVING 1=1',
                                            'quantidade_documentos_maior_que_having': "AND COUNT(DISTINCT ORCAMENTOS.NUMPED) > :quantidade_documentos_maior_que", },

        'coluna_quantidade_meses': {'quantidade_meses_campo_alias': "COUNT(DISTINCT TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM')) AS QUANTIDADE_MESES,", },
        'quantidade_meses_maior_que': {'having': 'HAVING 1=1',
                                       'quantidade_meses_maior_que_having': "AND COUNT(DISTINCT TO_CHAR(ORCAMENTOS.DATA_PEDIDO, 'YYYY-MM')) > :quantidade_meses_maior_que", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "ORCAMENTOS_ITENS.STATUS,",
                                            'status_produto_orcamento_campo': "ORCAMENTOS_ITENS.STATUS,", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "ORCAMENTOS_ITENS.STATUS = :chave_status_produto_orcamento AND", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "STATUS_ORCAMENTOS_ITENS.TIPO AS STATUS_TIPO,",
                                                 'status_produto_orcamento_tipo_campo': "STATUS_ORCAMENTOS_ITENS.TIPO,",
                                                 'status_produto_orcamento_tipo_from': orcamentos_status_produto_orcamento_tipo_from,
                                                 'status_produto_orcamento_tipo_join': orcamentos_status_produto_orcamento_tipo_join, },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "STATUS_ORCAMENTOS_ITENS.TIPO = :status_produto_orcamento_tipo AND" if kwargs_formulario.get('status_produto_orcamento_tipo') != "PERDIDO_CANCELADO" else "STATUS_ORCAMENTOS_ITENS.TIPO IN ('PERDIDO', 'CANCELADO') AND",
                                          'status_produto_orcamento_tipo_from': orcamentos_status_produto_orcamento_tipo_from,
                                          'status_produto_orcamento_tipo_join': orcamentos_status_produto_orcamento_tipo_join, },

        'coluna_rentabilidade': {'lfrete_coluna': orcamentos_lfrete_coluna,
                                 'lfrete_valor_coluna': orcamentos_lfrete_valor_coluna,
                                 'lfrete_from': orcamentos_lfrete_from,
                                 'lfrete_join': orcamentos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': orcamentos_lfrete_coluna,
                                       'lfrete_valor_coluna': orcamentos_lfrete_valor_coluna,
                                       'lfrete_from': orcamentos_lfrete_from,
                                       'lfrete_join': orcamentos_lfrete_join, },
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': orcamentos_lfrete_cor_coluna,
                                     'lfrete_from': orcamentos_lfrete_from,
                                     'lfrete_join': orcamentos_lfrete_join, },
        'coluna_aliquotas_itens': {'lfrete_coluna_aliquotas_itens': orcamentos_lfrete_aliquotas_itens_coluna,
                                   'lfrete_from': orcamentos_lfrete_from,
                                   'lfrete_join': orcamentos_lfrete_join, },
        'coluna_mc_cor_ajuste': {'mc_cor_ajuste_campo_alias': ", CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END AS MC_COR_AJUSTE",
                                 'mc_cor_ajuste_campo': "CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END,", },

        'coluna_pis': {'pis_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_PIS {conversao_moeda}) AS PIS,".format(conversao_moeda=conversao_moeda), },
        'coluna_cofins': {'cofins_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_COFINS {conversao_moeda}) AS COFINS,".format(conversao_moeda=conversao_moeda), },
        'coluna_icms': {'icms_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_ICMS {conversao_moeda}) AS ICMS,".format(conversao_moeda=conversao_moeda), },
        'coluna_icms_partilha': {'icms_partilha_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_ICMS_PARTILHA {conversao_moeda}) AS ICMS_PARTILHA,".format(conversao_moeda=conversao_moeda), },
        'coluna_ipi': {'ipi_campo_alias': "SUM(ORCAMENTOS_ITENS.VALOR_IPI {conversao_moeda}) AS IPI,".format(conversao_moeda=conversao_moeda), },
        'coluna_st': {'st_campo_alias': "SUM(ORCAMENTOS_ITENS.ICMS_SUBSTITUICAO_VALOR {conversao_moeda}) AS ST,".format(conversao_moeda=conversao_moeda), },
        'coluna_irpj_csll': {'irpj_csll_campo_alias': "SUM(ORCAMENTOS_ITENS.ANALISE_CONTRIBUICAO {conversao_moeda}) AS IRPJ_CSLL,".format(conversao_moeda=conversao_moeda), },

        'coluna_documento': {'documento_campo_alias': "ORCAMENTOS.NUMPED AS DOCUMENTO,",
                             'documento_campo': "ORCAMENTOS.NUMPED,", },
        'coluna_chave_documento': {'chave_documento_campo_alias': "ORCAMENTOS.CHAVE AS CHAVE_DOCUMENTO,",
                                   'chave_documento_campo': "ORCAMENTOS.CHAVE,", },
        'documento': {'documento_pesquisa': "ORCAMENTOS.NUMPED = :documento AND", },

        'coluna_log_nome_inclusao_documento': {'log_nome_inclusao_documento_campo_alias': "ORCAMENTOS.LOG_NOME_INCLUSAO AS LOG_NOME_INCLUSAO_DOCUMENTO,",
                                               'log_nome_inclusao_documento_campo': "ORCAMENTOS.LOG_NOME_INCLUSAO,", },

        'coluna_orcamento': {'orcamento_campo_alias': "",
                             'orcamento_campo': "",
                             'documentos_from': "",
                             'documentos_join': "", },
        'coluna_pedido': {'pedido_campo_alias': "DOCUMENTOS.PEDIDO,",
                          'pedido_campo': "DOCUMENTOS.PEDIDO,",
                          'documentos_from': orcamentos_documentos_from,
                          'documentos_join': orcamentos_documentos_join, },
        'coluna_nota': {'nota_campo_alias': "DOCUMENTOS.NOTA,",
                        'nota_campo': "DOCUMENTOS.NOTA,",
                        'documentos_from': orcamentos_documentos_from,
                        'documentos_join': orcamentos_documentos_join, },
        'coluna_log_nome_inclusao_orcamento': {'log_nome_inclusao_orcamento_campo_alias': "",
                                               'log_nome_inclusao_orcamento_campo': "",
                                               'documentos_from': "",
                                               'documentos_join': "", },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "ORCAMENTOS_ITENS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "ORCAMENTOS_ITENS.DATA_ENTREGA,", },
        'data_entrega_itens_maior_que': {'data_entrega_itens_maior_que_pesquisa': "ORCAMENTOS_ITENS.DATA_ENTREGA > :data_entrega_itens_maior_que AND", },
        'data_entrega_itens_menor_igual': {'data_entrega_itens_menor_igual_pesquisa': "ORCAMENTOS_ITENS.DATA_ENTREGA <= :data_entrega_itens_menor_igual AND", },

        'coluna_status_documento': {'status_documento_campo_alias': "ORCAMENTOS.STATUS AS STATUS_DOCUMENTO,",
                                    'status_documento_campo': "ORCAMENTOS.STATUS,", },
        'status_documento_em_aberto': {'status_documento_em_aberto_pesquisa': "ORCAMENTOS.STATUS IN ('EM ABERTO', 'BLOQUEADO') AND", },

        'coluna_orcamento_oportunidade': {'orcamento_oportunidade_campo_alias': "ORCAMENTOS.REGISTRO_OPORTUNIDADE AS OPORTUNIDADE,",
                                          'orcamento_oportunidade_campo': "ORCAMENTOS.REGISTRO_OPORTUNIDADE,", },

        'status_cliente_ativo': {'status_cliente_ativo_pesquisa': "CLIENTES.STATUS IN ('Y', 'P') AND", },

        'informacao_estrategica': {'informacao_estrategica_pesquisa': "EXISTS(SELECT CLIENTES_INFORMACOES_CLI.CHAVE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES.CODCLI = CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE AND CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO = :chave_informacao_estrategica) AND", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'coluna_peso_produto_proprio': {'peso_produto_proprio_campo_alias': "SUM(CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN ORCAMENTOS_ITENS.PESO_LIQUIDO ELSE 0 END) AS PESO_PP,", },

        'coluna_especie': {'especie_campo_alias': "",
                           'especie_campo': "", },
        'especie': {'especie_pesquisa': "", },

        'coluna_chave_transportadora': {'chave_transportadora_campo_alias': "ORCAMENTOS.CHAVE_TRANSPORTADORA AS CHAVE_TRANSPORTADORA,",
                                        'chave_transportadora_campo': "ORCAMENTOS.CHAVE_TRANSPORTADORA,", },
        'coluna_transportadora': {'transportadora_campo_alias': "TRANSPORTADORAS.NOMERED AS TRANSPORTADORA,",
                                  'transportadora_campo': "TRANSPORTADORAS.NOMERED,",
                                  'transportadoras_from': orcamentos_transportadoras_from,
                                  'transportadoras_join': orcamentos_transportadoras_join, },
        'transportadoras_geram_titulos': {'transportadoras_geram_titulos_pesquisa': "TRANSPORTADORAS.GERAR_TITULO_FRETE = 'SIM' AND",
                                          'transportadoras_from': orcamentos_transportadoras_from,
                                          'transportadoras_join': orcamentos_transportadoras_join, },

        'coluna_proximo_evento_grupo_economico': {'proximo_evento_grupo_economico_campo_alias': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_campo': "PROXIMO_EVENTO_GRUPO.PROXIMO_EVENTO_GRUPO,",
                                                  'proximo_evento_grupo_economico_from': orcamentos_proximo_evento_grupo_economico_from,
                                                  'proximo_evento_grupo_economico_join': orcamentos_proximo_evento_grupo_economico_join, },
        'desconsiderar_grupo_economico_com_evento_futuro': {'desconsiderar_grupo_economico_com_evento_futuro_pesquisa': "(PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO IS NULL OR PROXIMO_EVENTO_GRUPO.ULTIMO_EVENTO_GRUPO <= TRUNC(SYSDATE)) AND",
                                                            'proximo_evento_grupo_economico_from': orcamentos_proximo_evento_grupo_economico_from,
                                                            'proximo_evento_grupo_economico_join': orcamentos_proximo_evento_grupo_economico_join, },

        'coluna_destino_mercadorias': {'destino_mercadorias_campo_alias': "ORCAMENTOS.DESTINO AS DESTINO_MERCADORIAS,",
                                       'destino_mercadorias_campo': "ORCAMENTOS.DESTINO,", },

        'coluna_zona_franca_alc': {'zona_franca_alc_campo_alias': "CASE WHEN ORCAMENTOS.ZONA_FRANCA = 'SIM' OR ORCAMENTOS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END AS ZONA_FRANCA_ALC,",
                                   'zona_franca_alc_campo': "CASE WHEN ORCAMENTOS.ZONA_FRANCA = 'SIM' OR ORCAMENTOS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END,", },
    }

    # Itens de orçamento excluidos somente o que difere de orçamento

    orcamentos_itens_excluidos_status_produto_orcamento_tipo_from = orcamentos_status_produto_orcamento_tipo_from
    orcamentos_itens_excluidos_status_produto_orcamento_tipo_join = "STATUS_ORCAMENTOS_ITENS.DESCRICAO = ORCAMENTOS_ITENS_EXCLUIDOS.STATUS AND"

    orcamentos_itens_excluidos_lfrete_coluna = ", 0 AS MC"
    orcamentos_itens_excluidos_lfrete_valor_coluna = ", 0 AS MC_VALOR"
    orcamentos_itens_excluidos_lfrete_cor_coluna = ", 0 AS MC_COR, 0 AS MC_VALOR_COR"
    orcamentos_itens_excluidos_lfrete_aliquotas_itens_coluna = "0 AS ALIQUOTA_PIS, 0 AS ALIQUOTA_COFINS, 0 AS ALIQUOTA_ICMS, 0 AS ALIQUOTA_IR, 0 AS ALIQUOTA_CSLL, 0 AS ALIQUOTA_COMISSAO, 0 AS ALIQUOTA_DESPESA_ADM, 0 AS ALIQUOTA_DESPESA_COM, 0 AS ALIQUOTAS_TOTAIS,"
    orcamentos_itens_excluidos_lfrete_from = ""
    orcamentos_itens_excluidos_lfrete_join = ""

    orcamentos_itens_excluidos_valor_mercadorias = "(ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE * ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA) {conversao_moeda}".format(
        conversao_moeda=conversao_moeda)

    orcamentos_itens_excluidos_valor_mercadorias_mes_a_mes = ""
    if fonte == 'orcamentos' and trocar_para_itens_excluidos and coluna_mes_a_mes:
        for i, f in mes_a_mes:
            orcamentos_itens_excluidos_valor_mercadorias_mes_a_mes += f", SUM(CASE WHEN ORCAMENTOS.DATA_PEDIDO >= TO_DATE('{i}', 'YYYY-MM-DD') AND ORCAMENTOS.DATA_PEDIDO <= TO_DATE('{f}', 'YYYY-MM-DD') THEN {orcamentos_itens_excluidos_valor_mercadorias} ELSE 0 END) AS VALOR_{i.year}_{i.month:02d}"

    map_sql_orcamentos_base_itens_excluidos = {
        'valor_mercadorias': f"SUM({orcamentos_itens_excluidos_valor_mercadorias}) AS VALOR_MERCADORIAS",

        'fonte_itens': "COPLAS.ORCAMENTOS_ITENS_EXCLUIDOS,",

        'fonte_joins': """
            PRODUTOS.CPROD = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_PRODUTO AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE_ORCAMENTO AND
            ORCAMENTOS.CHAVE_JOB = JOBS.CODIGO AND
        """,
    }

    map_sql_orcamentos_itens_excluidos = {
        # coluna_custo_materia_prima_notas Não funciona com a fluxus, conferir se mudar a forma de beneficiamento
        'coluna_custo_materia_prima_notas': {'custo_materia_prima_notas_campo_alias': ""},

        'cfop_baixa_estoque': {'cfop_baixa_estoque_pesquisa': "", },

        'coluna_dias_decorridos': {'dias_decorridos_campo_alias': "0 AS DIAS_DECORRIDOS,"},

        'coluna_mes_a_mes': {'mes_a_mes_campo_alias': orcamentos_itens_excluidos_valor_mercadorias_mes_a_mes},

        'coluna_custo_total_item': {'custo_total_item_campo_alias': "0 AS CUSTO_TOTAL_ITEM,"},

        'coluna_valor_bruto': {'valor_bruto_campo_alias': "SUM((ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE * ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA) {conversao_moeda}) AS VALOR_BRUTO,".format(conversao_moeda=conversao_moeda)},

        'coluna_frete_incluso_item': {'frete_incluso_item_campo_alias': "0 AS FRETE_INCLUSO_ITEM,"},
        'coluna_frete_destacado': {'frete_destacado_campo_alias': "0 AS FRETE_DESTACADO,"},

        'valor_mercadorias_maior_igual': {'having': 'HAVING 1=1',
                                          'valor_mercadorias_maior_igual_having': "AND SUM((ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE * ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA) {conversao_moeda}) >= :valor_mercadorias_maior_igual".format(conversao_moeda=conversao_moeda), },

        'coluna_media_dia': {'media_dia_campo_alias': "0 AS MEDIA_DIA,"},

        'coluna_preco_tabela_inclusao': {'preco_tabela_inclusao_campo_alias': "0 AS PRECO_TABELA_INCLUSAO,", },

        'coluna_preco_venda_medio': {'preco_venda_medio_campo_alias': "0 AS PRECO_VENDA_MEDIO,", },

        'coluna_preco_venda': {'preco_venda_campo_alias': "ROUND(MAX(ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA {conversao_moeda}), 2) AS PRECO_VENDA,".format(conversao_moeda=conversao_moeda), },

        'coluna_desconto': {'desconto_campo_alias': "ROUND((1 - (ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA / ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_TABELA)) * 100, 2) AS DESCONTO,",
                            'desconto_campo': "ROUND((1 - (ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_VENDA / ORCAMENTOS_ITENS_EXCLUIDOS.PRECO_TABELA)) * 100, 2),", },

        'coluna_quantidade': {'quantidade_campo_alias': "SUM(ORCAMENTOS_ITENS_EXCLUIDOS.QUANTIDADE) AS QUANTIDADE,", },

        'desconsiderar_justificativas': {'desconsiderar_justificativa_pesquisa': "{} AND".format(justificativas(True)), },

        'coluna_quantidade_documentos': {'quantidade_documentos_campo_alias': "0 AS QUANTIDADE_DOCUMENTOS,", },

        'coluna_quantidade_meses': {'quantidade_meses_campo_alias': "0 AS QUANTIDADE_MESES,", },

        'coluna_status_produto_orcamento': {'status_produto_orcamento_campo_alias': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS,",
                                            'status_produto_orcamento_campo': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS,", },
        'status_produto_orcamento': {'status_produto_orcamento_pesquisa': "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS = :chave_status_produto_orcamento AND", },

        'coluna_status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_campo_alias': "STATUS_ORCAMENTOS_ITENS.TIPO AS STATUS_TIPO,",
                                                 'status_produto_orcamento_tipo_campo': "STATUS_ORCAMENTOS_ITENS.TIPO,",
                                                 'status_produto_orcamento_tipo_from': orcamentos_itens_excluidos_status_produto_orcamento_tipo_from,
                                                 'status_produto_orcamento_tipo_join': orcamentos_itens_excluidos_status_produto_orcamento_tipo_join, },
        'status_produto_orcamento_tipo': {'status_produto_orcamento_tipo_pesquisa': "STATUS_ORCAMENTOS_ITENS.TIPO = :status_produto_orcamento_tipo AND" if kwargs_formulario.get('status_produto_orcamento_tipo') != "PERDIDO_CANCELADO" else "STATUS_ORCAMENTOS_ITENS.TIPO IN ('PERDIDO', 'CANCELADO') AND",
                                          'status_produto_orcamento_tipo_from': orcamentos_itens_excluidos_status_produto_orcamento_tipo_from,
                                          'status_produto_orcamento_tipo_join': orcamentos_itens_excluidos_status_produto_orcamento_tipo_join, },

        'coluna_rentabilidade': {'lfrete_coluna': orcamentos_itens_excluidos_lfrete_coluna,
                                 'lfrete_valor_coluna': orcamentos_itens_excluidos_lfrete_valor_coluna,
                                 'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                 'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },
        'coluna_rentabilidade_valor': {'lfrete_coluna': orcamentos_itens_excluidos_lfrete_coluna,
                                       'lfrete_valor_coluna': orcamentos_itens_excluidos_lfrete_valor_coluna,
                                       'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                       'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },
        'coluna_rentabilidade_cor': {'lfrete_coluna_cor': orcamentos_itens_excluidos_lfrete_cor_coluna,
                                     'lfrete_from': orcamentos_itens_excluidos_lfrete_from,
                                     'lfrete_join': orcamentos_itens_excluidos_lfrete_join, },
        'coluna_aliquotas_itens': {'lfrete_coluna_aliquotas_itens': orcamentos_itens_excluidos_lfrete_aliquotas_itens_coluna,
                                   'lfrete_from': orcamentos_lfrete_from,
                                   'lfrete_join': orcamentos_lfrete_join, },
        'coluna_mc_cor_ajuste': {'mc_cor_ajuste_campo_alias': ", CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END AS MC_COR_AJUSTE",
                                 'mc_cor_ajuste_campo': "CASE WHEN PRODUTOS.CHAVE_FAMILIA = 7766 THEN (-1) WHEN PRODUTOS.CHAVE_FAMILIA IN (7767, 12441) THEN 4 WHEN PRODUTOS.CHAVE_FAMILIA = 8378 THEN 4 END,", },

        'coluna_pis': {'pis_campo_alias': "0 AS PIS,", },
        'coluna_cofins': {'cofins_campo_alias': "0 AS COFINS,", },
        'coluna_icms': {'icms_campo_alias': "0 AS ICMS,", },
        'coluna_icms_partilha': {'icms_partilha_campo_alias': "0 AS ICMS_PARTILHA,", },
        'coluna_ipi': {'ipi_campo_alias': "0 AS IPI,", },
        'coluna_st': {'st_campo_alias': "0 AS ST,", },
        'coluna_irpj_csll': {'irpj_csll_campo_alias': "0 AS IRPJ_CSLL,", },

        'coluna_data_entrega_itens': {'data_entrega_itens_campo_alias': "ORCAMENTOS.DATA_ENTREGA,",
                                      'data_entrega_itens_campo': "ORCAMENTOS.DATA_ENTREGA,", },
        'data_entrega_itens_maior_que': {'data_entrega_itens_maior_que_pesquisa': "ORCAMENTOS.DATA_ENTREGA > :data_entrega_itens_maior_que AND", },
        'data_entrega_itens_menor_igual': {'data_entrega_itens_menor_igual_pesquisa': "ORCAMENTOS.DATA_ENTREGA <= :data_entrega_itens_menor_igual AND", },

        'ordenar_sequencia_prioritario': {'sequencia_campo': "ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE,",
                                          'ordenar_sequencia_prioritario': "ORCAMENTOS_ITENS_EXCLUIDOS.CHAVE,", },

        'coluna_peso_produto_proprio': {'peso_produto_proprio_campo_alias': "0 AS PESO_PP,", },
    }

    sql_final = {}
    if fonte == 'orcamentos':
        sql_final.update(map_sql_orcamentos_base)
        if trocar_para_itens_excluidos:
            sql_final.update(map_sql_orcamentos_base_itens_excluidos)
    elif fonte == 'pedidos':
        sql_final.update(map_sql_pedidos_base)
    else:
        sql_final.update(map_sql_notas_base)

    for chave, valor in kwargs_formulario.items():
        if valor:
            if fonte == 'orcamentos':
                get_map_orcamento = map_sql_orcamentos.get(chave)
                if get_map_orcamento:
                    sql_final.update(get_map_orcamento)  # type:ignore
                    if trocar_para_itens_excluidos:
                        get_map_orcamento_itens_excluidos = map_sql_orcamentos_itens_excluidos.get(chave)
                        if get_map_orcamento_itens_excluidos:
                            sql_final.update(get_map_orcamento_itens_excluidos)  # type:ignore
            elif fonte == 'pedidos':
                get_map_pedido = map_sql_pedidos.get(chave)
                if get_map_pedido:
                    sql_final.update(get_map_pedido)  # type:ignore
            else:
                get_map_nota = map_sql_notas.get(chave)
                if get_map_nota:
                    sql_final.update(get_map_nota)  # type:ignore

    return sql_final


def get_relatorios_vendas(fonte: Literal['orcamentos', 'pedidos', 'faturamentos'], **kwargs):
    kwargs_sql = {}
    kwargs_sql_itens_excluidos = {}
    kwargs_ora = {}

    data_inicio = kwargs.get('inicio')
    data_fim = kwargs.get('fim')
    grupo_economico = kwargs.get('grupo_economico')
    carteira = kwargs.get('carteira')
    tipo_cliente = kwargs.get('tipo_cliente')
    familia_produto = kwargs.get('familia_produto')
    produto = kwargs.get('produto')
    produto_marca = kwargs.get('produto_marca')
    cidade = kwargs.get('cidade')
    estado = kwargs.get('estado')
    status_produto_orcamento = kwargs.get('status_produto_orcamento')
    status_produto_orcamento_tipo = kwargs.get('status_produto_orcamento_tipo')
    quantidade_documentos_maior_que = kwargs.get('quantidade_documentos_maior_que')
    quantidade_meses_maior_que = kwargs.get('quantidade_meses_maior_que')
    valor_mercadorias_maior_igual = kwargs.get('valor_mercadorias_maior_igual')
    documento = kwargs.get('documento')
    informacao_estrategica = kwargs.get('informacao_estrategica')
    job = kwargs.get('job')
    data_entrega_itens_maior_que = kwargs.get('data_entrega_itens_maior_que')
    data_entrega_itens_menor_igual = kwargs.get('data_entrega_itens_menor_igual')
    data_emissao_menor_que = kwargs.get('data_emissao_menor_que')
    especie = kwargs.get('especie')
    data_despacho_maior_igual = kwargs.get('data_despacho_maior_igual')
    data_despacho_menor_igual = kwargs.get('data_despacho_menor_igual')
    estoque_abc = kwargs.get('estoque_abc')
    data_vencimento_titulo_entre = kwargs.get('data_vencimento_titulo_entre')

    trocar_para_itens_excluidos = kwargs.pop('considerar_itens_excluidos', False)

    if not data_inicio:
        data_inicio = datetime.date(datetime(2010, 1, 1))

    if not data_fim:
        data_fim = datetime.date(datetime(2999, 12, 31))

    kwargs_sql.update(map_relatorio_vendas_sql_string_placeholders(fonte, **kwargs))
    if trocar_para_itens_excluidos and fonte == 'orcamentos':
        kwargs_sql_itens_excluidos.update(map_relatorio_vendas_sql_string_placeholders(
            fonte, trocar_para_itens_excluidos, **kwargs))  # type:ignore

    # kwargs_ora precisa conter os placeholders corretamente

    if grupo_economico:
        kwargs_ora.update({'grupo_economico': grupo_economico, })

    if carteira:
        chave_carteira = carteira if isinstance(carteira, int) else carteira.chave_analysis
        kwargs_ora.update({'chave_carteira': chave_carteira, })

    if tipo_cliente:
        chave_tipo_cliente = tipo_cliente if isinstance(tipo_cliente, int) else tipo_cliente.pk
        kwargs_ora.update({'chave_tipo_cliente': chave_tipo_cliente, })

    if familia_produto and not isinstance(familia_produto, list):
        chave_familia_produto = familia_produto if isinstance(familia_produto, int) else familia_produto.pk
        kwargs_ora.update({'chave_familia_produto': chave_familia_produto, })

    if produto:
        kwargs_ora.update({'produto': produto, })

    if produto_marca:
        chave_produto_marca = produto_marca if isinstance(produto_marca, int) else produto_marca.pk
        kwargs_ora.update({'chave_produto_marca': chave_produto_marca, })

    if cidade:
        kwargs_ora.update({'cidade': cidade, })

    if estado:
        chave_estado = estado if isinstance(estado, int) else estado.chave_analysis
        kwargs_ora.update({'chave_estado': chave_estado, })

    if status_produto_orcamento:
        if fonte == 'orcamentos':
            chave_status_produto_orcamento = status_produto_orcamento.DESCRICAO
            kwargs_ora.update({'chave_status_produto_orcamento': chave_status_produto_orcamento, })

    if status_produto_orcamento_tipo:
        if fonte == 'orcamentos':
            if status_produto_orcamento_tipo != "PERDIDO_CANCELADO":
                kwargs_ora.update({'status_produto_orcamento_tipo': status_produto_orcamento_tipo, })

    if quantidade_documentos_maior_que:
        kwargs_ora.update({'quantidade_documentos_maior_que': quantidade_documentos_maior_que})

    if quantidade_meses_maior_que:
        kwargs_ora.update({'quantidade_meses_maior_que': quantidade_meses_maior_que})

    if valor_mercadorias_maior_igual:
        kwargs_ora.update({'valor_mercadorias_maior_igual': valor_mercadorias_maior_igual})

    if documento:
        kwargs_ora.update({'documento': documento})

    if informacao_estrategica:
        chave_informacao_estrategica = informacao_estrategica if isinstance(
            informacao_estrategica, int) else informacao_estrategica.pk
        kwargs_ora.update({'chave_informacao_estrategica': chave_informacao_estrategica, })

    if job:
        chave_job = job if isinstance(job, int) else job.pk
        kwargs_ora.update({'chave_job': chave_job, })

    if data_entrega_itens_maior_que:
        kwargs_ora.update({'data_entrega_itens_maior_que': data_entrega_itens_maior_que})

    if data_entrega_itens_menor_igual:
        kwargs_ora.update({'data_entrega_itens_menor_igual': data_entrega_itens_menor_igual})

    if data_emissao_menor_que:
        kwargs_ora.update({'data_emissao_menor_que': data_emissao_menor_que})

    if especie:
        kwargs_ora.update({'especie': especie})

    if data_despacho_maior_igual:
        kwargs_ora.update({'data_despacho_maior_igual': data_despacho_maior_igual})

    if data_despacho_menor_igual:
        kwargs_ora.update({'data_despacho_menor_igual': data_despacho_menor_igual})

    if estoque_abc:
        kwargs_ora.update({'estoque_abc': estoque_abc})

    if data_vencimento_titulo_entre:
        data_vencimento_titulo_inicio, data_vencimento_titulo_fim = data_vencimento_titulo_entre
        kwargs_ora.update({'data_vencimento_titulo_inicio': data_vencimento_titulo_inicio})
        kwargs_ora.update({'data_vencimento_titulo_fim': data_vencimento_titulo_fim})

    sql_base = """
        SELECT
            {job_campo_alias}
            {dias_decorridos_campo_alias}
            {data_emissao_campo_alias}
            {data_despacho_campo_alias}
            {data_entrega_itens_campo_alias}
            {data_saida_campo_alias}
            {ano_mes_emissao_campo_alias}
            {ano_emissao_campo_alias}
            {mes_emissao_campo_alias}
            {dia_emissao_campo_alias}
            {chave_documento_campo_alias}
            {documento_campo_alias}
            {especie_campo_alias}
            {parcelas_campo_alias}
            {log_nome_inclusao_documento_campo_alias}
            {orcamento_campo_alias}
            {log_nome_inclusao_orcamento_campo_alias}
            {pedido_campo_alias}
            {nota_campo_alias}
            {orcamento_oportunidade_campo_alias}
            {status_documento_campo_alias}
            {peso_bruto_nota_campo_alias}
            {representante_campo_alias}
            {representante_documento_campo_alias}
            {segundo_representante_campo_alias}
            {segundo_representante_documento_campo_alias}
            {carteira_campo_alias}
            {grupo_economico_campo_alias}
            {cliente_campo_alias}
            {cgc_campo_alias}
            {inscricao_estadual_campo_alias}
            {proximo_evento_grupo_economico_campo_alias}
            {quantidade_documentos_campo_alias}
            {quantidade_meses_campo_alias}
            {estado_origem_campo_alias}
            {estado_campo_alias}
            {cidade_campo_alias}
            {estado_destino_campo_alias}
            {cidade_destino_campo_alias}
            {destino_mercadorias_campo_alias}
            {zona_franca_alc_campo_alias}
            {tipo_cliente_campo_alias}
            {chave_transportadora_campo_alias}
            {transportadora_campo_alias}
            {cobranca_frete_campo_alias}
            {familia_produto_campo_alias}
            {estoque_abc_campo_alias}
            {chave_produto_campo_alias}
            {produto_campo_alias}
            {unidade_campo_alias}
            {status_produto_orcamento_campo_alias}
            {status_produto_orcamento_tipo_campo_alias}
            {preco_tabela_inclusao_campo_alias}
            {preco_venda_medio_campo_alias}
            {preco_venda_campo_alias}
            {desconto_campo_alias}
            {quantidade_campo_alias}
            {peso_produto_proprio_campo_alias}
            {quantidade_volumes_campo_alias}
            {media_dia_campo_alias}
            {frete_destacado_campo_alias}
            {frete_incluso_item_campo_alias}
            {custo_total_item_campo_alias}
            {lfrete_coluna_aliquotas_itens}
            {ipi_campo_alias}
            {st_campo_alias}
            {pis_campo_alias}
            {cofins_campo_alias}
            {icms_campo_alias}
            {icms_partilha_campo_alias}
            {irpj_csll_campo_alias}
            {valor_bruto_campo_alias}
            {custo_materia_prima_notas_campo_alias}

            {valor_mercadorias}

            {lfrete_coluna}
            {lfrete_valor_coluna}
            {lfrete_coluna_cor}
            {mc_cor_ajuste_campo_alias}

            {mes_a_mes_campo_alias}

        FROM
            {lfrete_from}
            {notas_peso_liquido_from}
            {status_produto_orcamento_tipo_from}
            {destino_from}
            {transportadoras_from}
            {documentos_from}
            {proximo_evento_grupo_economico_from}
            {representantes_from}
            {representantes_documento_from}
            {segundo_representantes_from}
            {segundo_representantes_documento_from}
            COPLAS.VENDEDORES,
            {fonte_itens}
            {fonte}
            COPLAS.FAMILIA_PRODUTOS,
            COPLAS.PRODUTOS,
            COPLAS.UNIDADES,
            COPLAS.GRUPO_ECONOMICO,
            COPLAS.CLIENTES,
            COPLAS.CLIENTES_TIPOS,
            COPLAS.ESTADOS,
            COPLAS.JOBS

        WHERE
            {lfrete_join}
            {status_produto_orcamento_tipo_join}
            {destino_join}
            {transportadoras_join}
            {documentos_join}
            {proximo_evento_grupo_economico_join}
            {representantes_join}
            {representantes_documento_join}
            {segundo_representantes_join}
            {segundo_representantes_documento_join}
            PRODUTOS.CHAVE_UNIDADE = UNIDADES.CHAVE AND
            FAMILIA_PRODUTOS.CHAVE = PRODUTOS.CHAVE_FAMILIA AND
            CLIENTES.UF = ESTADOS.CHAVE AND
            {fonte_joins}
            CLIENTES.CHAVE_TIPO = CLIENTES_TIPOS.CHAVE AND
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES.CHAVE_GRUPOECONOMICO = GRUPO_ECONOMICO.CHAVE(+) AND
            {fonte_where}

            {grupo_economico_pesquisa}
            {carteira_pesquisa}
            {tipo_cliente_pesquisa}
            {familia_produto_pesquisa}
            {produto_pesquisa}
            {cidade_pesquisa}
            {estado_pesquisa}
            {nao_compraram_depois_pesquisa}
            {status_produto_orcamento_pesquisa}
            {status_produto_orcamento_tipo_pesquisa}
            {desconsiderar_justificativa_pesquisa}
            {status_documento_em_aberto_pesquisa}
            {carteira_parede_de_concreto_pesquisa}
            {carteira_premoldado_poste_pesquisa}
            {status_cliente_ativo_pesquisa}
            {documento_pesquisa}
            {informacao_estrategica_pesquisa}
            {job_pesquisa}
            {data_entrega_itens_maior_que_pesquisa}
            {data_entrega_itens_menor_igual_pesquisa}
            {data_emissao_menor_que_pesquisa}
            {especie_pesquisa}
            {cobranca_frete_cif_pesquisa}
            {transportadoras_geram_titulos_pesquisa}
            {data_despacho_maior_igual_pesquisa}
            {data_despacho_menor_igual_pesquisa}
            {desconsiderar_grupo_economico_com_evento_futuro_pesquisa}
            {estoque_abc_pesquisa}
            {cfop_baixa_estoque_pesquisa}
            {produto_marca_pesquisa}
            {data_vencimento_titulo_entre_pesquisa}

            {fonte_where_data}

        GROUP BY
            {job_campo}
            {sequencia_campo}
            {data_emissao_campo}
            {data_despacho_campo}
            {data_entrega_itens_campo}
            {ano_mes_emissao_campo}
            {ano_emissao_campo}
            {mes_emissao_campo}
            {dia_emissao_campo}
            {chave_documento_campo}
            {documento_campo}
            {orcamento_oportunidade_campo}
            {status_documento_campo}
            {carteira_campo}
            {grupo_economico_campo}
            {cliente_campo}
            {tipo_cliente_campo}
            {familia_produto_campo}
            {produto_campo}
            {unidade_campo}
            {status_produto_orcamento_campo}
            {status_produto_orcamento_tipo_campo}
            {cidade_campo}
            {estado_campo}
            {desconto_campo}
            {lfrete_coluna_aliquotas_itens}
            {mc_cor_ajuste_campo}
            {chave_transportadora_campo}
            {estado_origem_campo}
            {estado_destino_campo}
            {cidade_destino_campo}
            {destino_mercadorias_campo}
            {zona_franca_alc_campo}
            {chave_produto_campo}
            {data_saida_campo}
            {quantidade_volumes_campo}
            {peso_bruto_nota_campo}
            {transportadora_campo}
            {cobranca_frete_campo}
            {orcamento_campo}
            {pedido_campo}
            {nota_campo}
            {log_nome_inclusao_documento_campo}
            {proximo_evento_grupo_economico_campo}
            {cgc_campo}
            {inscricao_estadual_campo}
            {estoque_abc_campo}
            {parcelas_campo}
            {log_nome_inclusao_orcamento_campo}
            {representante_campo}
            {representante_documento_campo}
            {segundo_representante_campo}
            {segundo_representante_documento_campo}
            {especie_campo}
            1

        {having}
            {quantidade_documentos_maior_que_having}
            {quantidade_meses_maior_que_having}
            {valor_mercadorias_maior_igual_having}

        ORDER BY
            {ordenar_sequencia_prioritario}
            {ordenar_valor_descrescente_prioritario}

            {job_campo}
            {ano_mes_emissao_campo}
            {ano_emissao_campo}
            {mes_emissao_campo}
            {dia_emissao_campo}
            {documento_campo}
            {carteira_campo}
            {tipo_cliente_campo}
            {familia_produto_campo}
            {proporcao_campo}
            {estoque_abc_campo}
            {produto_campo}
            {status_produto_orcamento_campo}
            {status_produto_orcamento_tipo_campo}
            VALOR_MERCADORIAS DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, data_fim=data_fim, **kwargs_ora)

    if trocar_para_itens_excluidos and fonte == 'orcamentos':
        sql_itens_excluidos = sql_base.format_map(DefaultDict(kwargs_sql_itens_excluidos))
        resultado_itens_excluidos = executar_oracle(sql_itens_excluidos, exportar_cabecalho=True,
                                                    data_inicio=data_inicio, data_fim=data_fim, **kwargs_ora)

        dt_resultado = pd.DataFrame(resultado)
        dt_resultado_itens_excluidos = pd.DataFrame(resultado_itens_excluidos)

        dt_resultado_final = pd.concat([dt_resultado, dt_resultado_itens_excluidos])

        alias_para_header_groupby = ['DATA_EMISSAO', 'ANO_EMISSAO', 'MES_EMISSAO', 'DIA_EMISSAO', 'ANO_MES_EMISSAO',
                                     'CHAVE_GRUPO_ECONOMICO', 'GRUPO', 'CARTEIRA', 'TIPO_CLIENTE', 'FAMILIA_PRODUTO',
                                     'PRODUTO', 'UNIDADE', 'CIDADE_PRINCIPAL', 'UF_PRINCIPAL', 'STATUS', 'STATUS_TIPO',
                                     'DOCUMENTO', 'CLIENTE', 'DATA_ENTREGA', 'STATUS_DOCUMENTO', 'OPORTUNIDADE',
                                     'DESCONTO', 'ALIQUOTA_PIS', 'ALIQUOTA_COFINS', 'ALIQUOTA_ICMS',
                                     'ALIQUOTA_IR', 'ALIQUOTA_CSLL', 'ALIQUOTA_COMISSAO', 'ALIQUOTA_DESPESA_ADM',
                                     'ALIQUOTA_DESPESA_COM', 'ALIQUOTAS_TOTAIS', 'MC_COR_AJUSTE', 'JOB',
                                     'CHAVE_TRANSPORTADORA', 'UF_ORIGEM', 'UF_DESTINO', 'CIDADE_DESTINO',
                                     'DESTINO_MERCADORIAS', 'ZONA_FRANCA_ALC', 'CHAVE_PRODUTO', 'DATA_SAIDA',
                                     'VOLUMES_QUANTIDADE', 'PESO_BRUTO_NOTA', 'TRANSPORTADORA', 'COBRANCA_FRETE',
                                     'ORCAMENTO', 'PEDIDO', 'NOTA', 'DATA_DESPACHO', 'LOG_NOME_INCLUSAO_DOCUMENTO',
                                     'PROXIMO_EVENTO_GRUPO', 'CGC', 'INSCRICAO_ESTADUAL', 'ESTOQUE_ABC', 'PARCELAS',
                                     'LOG_INCLUSAO_ORCAMENTO', 'REPRESENTANTE', 'REPRESENTANTE_DOCUMENTO',
                                     'SEGUNDO_REPRESENTANTE', 'SEGUNDO_REPRESENTANTE_DOCUMENTO', 'ESPECIE',
                                     'CHAVE_DOCUMENTO',]
        # Em caso de não ser só soma para juntar os dataframes com sum(), usar em caso the agg()
        # alias_para_header_agg = {'VALOR_MERCADORIAS': 'sum', 'MC': 'sum', 'MC_VALOR': 'sum', 'MEDIA_DIA': 'sum',
        #                          'PRECO_TABELA_INCLUSAO': 'sum', 'PRECO_VENDA_MEDIO': 'sum', 'QUANTIDADE': 'sum',
        #                          'QUANTIDADE_DOCUMENTOS': 'sum', }
        cabecalhos = list(dt_resultado_final.columns)

        alias_para_header_groupby = [header for header in alias_para_header_groupby if header in cabecalhos]
        # Em caso de não ser só soma para juntar os dataframes com sum(), usar em caso the agg()
        # alias_para_header_agg = {key: value for key, value in alias_para_header_agg.items() if key in cabecalhos}

        if alias_para_header_groupby:
            dt_resultado_final = dt_resultado_final.groupby(alias_para_header_groupby).sum().reset_index()
            dt_resultado_final = dt_resultado_final.sort_values(by='VALOR_MERCADORIAS', ascending=False)
            resultado = dt_resultado_final.to_dict(orient='records')
        else:
            dt_resultado_final = dt_resultado_final.sum()
            resultado = [dt_resultado_final.to_dict()]

    return resultado


def get_email_contatos(condicao):
    sql = """
        SELECT DISTINCT
            RTRIM(LTRIM(CONTATOS.EMAIL)) AS EMAIL

        FROM
            COPLAS.CONTATOS,
            COPLAS.CLIENTES

        WHERE
            CLIENTES.CODCLI = CONTATOS.CHAVE_CLIENTE AND

            {condicao} AND

            CONTATOS.ATIVO = 'SIM' AND
            CONTATOS.ENVIAR_MALA = 'SIM' AND
            CLIENTES.STATUS IN ('Y', 'P') AND
            CONTATOS.CHAVE NOT IN (
                SELECT
                    CHAVE

                FROM
                    COPLAS.CONTATOS

                WHERE
                    EMAIL LIKE '% %' OR
                    EMAIL NOT LIKE '%_@_%' OR
                    EMAIL LIKE '%,%' OR
                    EMAIL LIKE '%>%' OR
                    EMAIL LIKE '%<%' OR
                    EMAIL LIKE '.%' OR
                    EMAIL LIKE '%.' OR
                    EMAIL LIKE '%..%' OR
                    EMAIL LIKE '%"%' OR
                    EMAIL LIKE '%(%' OR
                    EMAIL LIKE '%)%' OR
                    EMAIL LIKE '%;%' OR
                    EMAIL LIKE '%\\%' OR
                    EMAIL LIKE '%[%' OR
                    EMAIL LIKE '%]%' OR
                    EMAIL LIKE '%!%' OR
                    EMAIL LIKE '%#%' OR
                    EMAIL LIKE '%$%' OR
                    EMAIL LIKE '%*%' OR
                    EMAIL LIKE '%/%' OR
                    EMAIL LIKE '%?%' OR
                    EMAIL LIKE '%{{%' OR
                    EMAIL LIKE '%}}%' OR
                    EMAIL LIKE '%|%' OR
                    EMAIL IS NULL
            )

        ORDER BY
            EMAIL
    """

    sql = sql.format(condicao=condicao)

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    return resultado
