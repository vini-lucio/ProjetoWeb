from analysis.models import CLIENTES
from dashboards.services import get_relatorios_vendas
from dashboards.services_financeiro import get_relatorios_financeiros
from django.db.models import Count
from django.utils import timezone
from marketing.models import LeadsRdStation
from datetime import datetime
from utils.plotly_parametros import update_layout_kwargs
import pandas as pd
import plotly.express as px
import plotly.io as pio


class DashBoardMarketing():
    """Gera dashboards de marketing base"""

    def __init__(self, data_inicio, data_fim, fechado_inicio, fechado_fim) -> None:
        """
        Parametros:
        -----------
        :data_inicio [Date]: com a data inicial da criação do lead
        :data_fim [Date]: com a data final da criação do lead
        :fechado_inicio [Date]: com a data inicial dos orçamentos fechados
        :fechado_fim [Date]: com a data final dos orçamentos fechados
        """
        data_hora_inicio = datetime(data_inicio.year, data_inicio.month, data_inicio.day, 0, 0, 0)
        data_hora_inicio = timezone.make_aware(data_hora_inicio)
        data_hora_fim = datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59)
        data_hora_fim = timezone.make_aware(data_hora_fim)

        leads = LeadsRdStation.objects.filter(criado_em__gte=data_hora_inicio).filter(criado_em__lte=data_hora_fim)
        self.leads_validos = leads.filter(lead_valido=True)

        # Inclui novos atributos aos leads temporariamente
        # for lead in self.leads_validos:
        #     lead.valor_orcamentos_perdidos = 0  # type:ignore
        #     lead.valor_orcamentos_em_abertos = 0  # type:ignore
        #     lead.valor_orcamentos_fechados = 0  # type:ignore

        #     if lead.chave_analysis:
        #         orcamentos = get_relatorios_vendas('orcamentos', inicio=data_inicio, fim=data_fim,
        #                                            coluna_status_produto_orcamento_tipo=True,
        #                                            chave_cliente=lead.chave_analysis)
        #         for status in orcamentos:
        #             tipo = status['STATUS_TIPO']
        #             valor = status['VALOR_MERCADORIAS']
        #             if tipo == 'FECHADO':
        #                 lead.valor_orcamentos_fechados += valor  # type: ignore
        #                 continue
        #             if tipo == 'EM ABERTO':
        #                 lead.valor_orcamentos_em_abertos += valor  # type: ignore
        #                 continue
        #             lead.valor_orcamentos_perdidos += valor  # type: ignore

        canais = self.leads_validos.values('origem').annotate(leads=Count('pk')).order_by('-leads')
        id_clientes_leads_validos = self.leads_validos.filter(
            chave_analysis__isnull=False).values_list('chave_analysis', flat=True)
        id_clientes_leads_validos = list(id_clientes_leads_validos)

        self.quantidade_leads_total = leads.count()
        self.quantidade_leads_validos = self.leads_validos.count()
        self.quantidade_leads_por_canal_origem = canais
        self.quantidade_leads_por_regiao = CLIENTES.objects.filter(pk__in=id_clientes_leads_validos).values(
            'CHAVE_VENDEDOR3__NOMERED').annotate(LEADS=Count('pk')).order_by('-LEADS')

        investimentos = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_inicio,
                                                   data_liquidacao_fim=data_fim, fornecedor='RESULTADOS DIGITAIS')
        investimentos = investimentos[0]['VALOR_EFETIVO'] if investimentos else 0
        self.investimentos = investimentos

        orcamentos_fechados = None
        if id_clientes_leads_validos:
            # TODO: considerar somente cadastros que nunca compraram antes da criação do lead?
            orcamentos_fechados = get_relatorios_vendas('orcamentos', inicio=fechado_inicio, fim=fechado_fim,
                                                        coluna_quantidade_clientes=True,
                                                        status_produto_orcamento='FECHADO',
                                                        chave_cliente=id_clientes_leads_validos)
            orcamentos_fechados = orcamentos_fechados[0] if orcamentos_fechados else None
        self.quantidade_leads_compraram = orcamentos_fechados['QUANTIDADE_CLIENTES'] if orcamentos_fechados else 0
        self.orcamentos_fechados = orcamentos_fechados['VALOR_MERCADORIAS'] if orcamentos_fechados else 0

        self.taxa_conversao = 0
        if self.quantidade_leads_validos:
            self.taxa_conversao = self.quantidade_leads_compraram / self.quantidade_leads_validos * 100
        self.custo_por_lead = 0
        if self.quantidade_leads_total:
            self.custo_por_lead = self.investimentos / self.quantidade_leads_total
        self.roas = 0
        if self.investimentos:
            self.roas = self.orcamentos_fechados / self.investimentos * 100

        # Geração de graficos
        dados_grafico_leads_por_canal_origem = pd.DataFrame(self.quantidade_leads_por_canal_origem)
        if not dados_grafico_leads_por_canal_origem.empty:
            grafico_leads_por_canal_origem = px.pie(dados_grafico_leads_por_canal_origem, values='leads',
                                                    names='origem', title='Leads por Canal de Origem')
            grafico_leads_por_canal_origem.update_layout(update_layout_kwargs, paper_bgcolor='rgb(238, 238, 238)',
                                                         legend_orientation='v', height=400, width=540)
            self.grafico_leads_por_canal_origem_html = pio.to_html(grafico_leads_por_canal_origem, full_html=False)

        dados_grafico_leads_por_regiao = pd.DataFrame(self.quantidade_leads_por_regiao)
        if not dados_grafico_leads_por_regiao.empty:
            grafico_leads_por_regiao = px.pie(dados_grafico_leads_por_regiao, values='LEADS',
                                              names='CHAVE_VENDEDOR3__NOMERED',
                                              title='Leads por Região')
            grafico_leads_por_regiao.update_layout(update_layout_kwargs, paper_bgcolor='rgb(238, 238, 238)',
                                                   legend_orientation='v', height=400, width=540)
            self.grafico_leads_por_regiao_html = pio.to_html(grafico_leads_por_regiao, full_html=False)
