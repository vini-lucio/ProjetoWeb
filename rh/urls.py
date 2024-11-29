from django.urls import path
from rh.views import (index, ReciboValeTransporteListView, FeriasEmAbertoListView, SolicitacaoFeriasDetailView,
                      DependentesIrListView)

app_name = 'rh'

urlpatterns = [
    path('', index, name='index'),
    path('recibo-vale-transporte/', ReciboValeTransporteListView.as_view(), name='recibo-vale-transporte'),
    path('ferias-em-aberto/', FeriasEmAbertoListView.as_view(), name='ferias-em-aberto'),
    path('solicitacao-ferias/<int:pk>/', SolicitacaoFeriasDetailView.as_view(), name='solicitacao-ferias'),
    path('dependentes-ir/', DependentesIrListView.as_view(), name='dependentes-ir'),
]
