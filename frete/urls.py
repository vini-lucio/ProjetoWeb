from django.urls import path
from frete.views import calculo_frete, prazos, MedidasProdutos, relatorios, volumes_manual

app_name = 'frete'

urlpatterns = [
    path('', calculo_frete, name='calculo-frete'),
    path('prazos/', prazos, name='prazos'),
    path('medidas-produtos/', MedidasProdutos.as_view(), name='medidas-produtos'),
    path('relatorios/', relatorios, name='relatorios'),
    path('volumes-manual/', volumes_manual, name='volumes-manual'),
]
