from django.urls import path
from dashboards.views import vendas_tv, vendas_supervisao, relatorios_supervisao, vendas

app_name = 'dashboards'

urlpatterns = [
    path('vendas/', vendas, name='vendas'),
    path('vendas-tv/', vendas_tv, name='vendas-tv'),
    path('vendas-supervisao/', vendas_supervisao, name='vendas-supervisao'),
    path('relatorios-supervisao/<str:fonte>/', relatorios_supervisao, name='relatorios-supervisao'),
]

# TODO: atalhos para dashboards
