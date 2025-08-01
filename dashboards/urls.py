from django.urls import path
from dashboards.views import (vendas_tv, vendas_supervisao, relatorios_supervisao, vendas_carteira, eventos_dia,
                              listagens, analise_orcamentos, eventos_por_dia, detalhes_dia)

app_name = 'dashboards'

urlpatterns = [
    path('vendas-tv/', vendas_tv, name='vendas-tv'),
    path('vendas-carteira/', vendas_carteira, name='vendas-carteira'),
    path('vendas-carteira/detalhes-dia/', detalhes_dia, name='detalhes-dia'),
    path('vendas-carteira/eventos-dia/', eventos_dia, name='eventos-dia'),
    path('vendas-carteira/eventos-por-dia/', eventos_por_dia, name='eventos-por-dia'),
    path('vendas-carteira/listagens/<str:listagem>/', listagens, name='listagens'),
    path('vendas-supervisao/', vendas_supervisao, name='vendas-supervisao'),
    path('relatorios-supervisao/<str:fonte>/', relatorios_supervisao, name='relatorios-supervisao'),
    path('analise-orcamentos/', analise_orcamentos, name='analise-orcamentos'),
]
