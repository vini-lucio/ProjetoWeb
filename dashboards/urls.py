from django.urls import path
from dashboards.views import vendas_tv, vendas_supervisao, relatorios_supervisao, vendas_carteira

app_name = 'dashboards'

urlpatterns = [
    path('vendas-tv/', vendas_tv, name='vendas-tv'),
    path('vendas-carteira/', vendas_carteira, name='vendas-carteira'),
    path('vendas-supervisao/', vendas_supervisao, name='vendas-supervisao'),
    path('relatorios-supervisao/<str:fonte>/', relatorios_supervisao, name='relatorios-supervisao'),
]

# TODO: atalhos para dashboards
