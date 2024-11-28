from django.urls import path
from rh.views import index, ReciboValeTransporteListView, FeriasEmAbertoListView

app_name = 'rh'

urlpatterns = [
    path('', index, name='index'),
    path('recibo-vale-transporte/', ReciboValeTransporteListView.as_view(), name='recibo-vale-transporte'),
    path('ferias-em-aberto/', FeriasEmAbertoListView.as_view(), name='ferias-em-aberto'),
]
