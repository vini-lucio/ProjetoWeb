from analysis.models import CLIENTES
from dashboards.services import get_relatorios_vendas
from dashboards.services_financeiro import get_relatorios_financeiros
from django.db.models import Count
from django.utils import timezone
from marketing.models import LeadsRdStation
from datetime import datetime


class DashBoardMarketing():
    """Gera dashboards de marketing base"""

    # TODO: dados de orçamentos por grupo economico?

    def __init__(self, data_inicio, data_fim) -> None:
        """
        Parametros:
        -----------
        :data_inicio [Date]: com a data inicial.
        :data_fim [Date]: com a data final
        """
        data_hora_inicio = datetime(data_inicio.year, data_inicio.month, data_inicio.day, 0, 0, 0)
        data_hora_inicio = timezone.make_aware(data_hora_inicio)
        data_hora_fim = datetime(data_fim.year, data_fim.month, data_fim.day, 23, 59, 59)
        data_hora_fim = timezone.make_aware(data_hora_fim)

        leads = LeadsRdStation.objects.filter(criado_em__gte=data_hora_inicio).filter(criado_em__lte=data_hora_fim)
        leads_validos = leads.filter(lead_valido=True)

        canais = leads_validos.values('origem').annotate(leads=Count('pk')).order_by('-leads')
        id_clientes_leads_validos = leads_validos.filter(
            chave_analysis__isnull=False).values_list('chave_analysis', flat=True)
        id_clientes_leads_validos = list(id_clientes_leads_validos)

        self.quantidade_leads_total = leads.count()
        self.quantidade_leads_qualificados = leads_validos.count()
        self.quantidade_leads_por_canal_origem = canais
        self.quantidade_leads_por_regiao = CLIENTES.objects.filter(pk__in=id_clientes_leads_validos).values(
            'CHAVE_VENDEDOR3__NOMERED').annotate(LEADS=Count('pk')).order_by('-LEADS')

        investimento = get_relatorios_financeiros('pagar', data_liquidacao_inicio=data_inicio,
                                                  data_liquidacao_fim=data_fim, fornecedor='RESULTADOS DIGITAIS')
        investimento = investimento[0]['VALOR_EFETIVO'] if investimento else 0
        self.valor_investimento = investimento

        faturamentos = None
        if id_clientes_leads_validos:
            faturamentos = get_relatorios_vendas('faturamentos', inicio=data_inicio, fim=data_fim,
                                                 coluna_quantidade_clientes=True,
                                                 chave_cliente=id_clientes_leads_validos)
            faturamentos = faturamentos[0] if faturamentos else None
        self.quantidade_leads_compraram = faturamentos['QUANTIDADE_CLIENTES'] if faturamentos else 0
        self.valor_faturamento = faturamentos['VALOR_MERCADORIAS'] if faturamentos else 0

        self.taxa_conversao = 0
        if self.quantidade_leads_qualificados:
            self.taxa_conversao = self.quantidade_leads_compraram / self.quantidade_leads_qualificados * 100
        self.custo_por_lead = 0
        if self.quantidade_leads_total:
            self.custo_por_lead = self.valor_investimento / self.quantidade_leads_total
        self.roas = 0
        if self.valor_investimento:
            self.roas = self.valor_faturamento / self.valor_investimento * 100
