from django.urls import path
from dashboards.views import vendas_tv, vendas_supervisao

app_name = 'dashboards'

urlpatterns = [
    path('vendas-tv/', vendas_tv, name='vendas-tv'),
    path('vendas-supervisao/', vendas_supervisao, name='vendas-supervisao'),
]

# TODO: atalhos para dashboards
