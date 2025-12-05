from django.urls import path
from home.views import IndexListView
from .views import relatorios_rnc

app_name = 'vendas'

urlpatterns = [
    path('', IndexListView.as_view(), name='vendas'),
    path('relatorios-rnc/', relatorios_rnc, name='relatorios-rnc'),
]
