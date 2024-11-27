from django.urls import path
from rh.views import index, ReciboValeTransporteListView

app_name = 'rh'

urlpatterns = [
    path('', index, name='index'),
    path('recibo-vale-transporte/', ReciboValeTransporteListView.as_view(), name='recibo-vale-transporte'),
]
