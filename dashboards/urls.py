from django.urls import path
from dashboards.views import vendas_tv

app_name = 'dashboards'

urlpatterns = [
    path('vendas-tv/', vendas_tv, name='vendas-tv'),
]
