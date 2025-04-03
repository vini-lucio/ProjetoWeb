# from django.shortcuts import render
from django.views.generic import DetailView
from analysis.models import GRUPO_ECONOMICO
from dashboards.services import get_relatorios_vendas


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

        quantidade_clientes = objeto.quantidade_clientes_ativos  # type:ignore
        quantidade_tipos = objeto.quantidade_clientes_ativos_por_tipo  # type:ignore
        quantidade_carteiras = objeto.quantidade_clientes_ativos_por_carteira  # type:ignore
        quantidade_eventos_em_aberto = objeto.quantidade_eventos_em_aberto  # type:ignore

        historico_faturamento_anual = get_relatorios_vendas(
            orcamento=False,
            grupo_economico=objeto.DESCRICAO,  # type: ignore
            coluna_ano_emissao=True,
            coluna_quantidade_documentos=True,
        )

        context.update({
            'titulo_pagina': titulo_pagina,
            'quantidade_clientes': quantidade_clientes,
            'quantidade_tipos': quantidade_tipos,
            'quantidade_carteiras': quantidade_carteiras,
            'historico_faturamento_anual': historico_faturamento_anual,
            'quantidade_eventos_em_aberto': quantidade_eventos_em_aberto,
        })
        return context
