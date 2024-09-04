from django.urls import path
from home.views import (IndexListView, HomeLinkDetailView, ConsultoriaVendasListView,
                        calculo_piso_elevado, calculo_quimicos, calculo_niveladores)

app_name = 'home'

urlpatterns = [
    path('', IndexListView.as_view(), name='index'),
    path('home_link/<slug:slug>/', HomeLinkDetailView.as_view(), name='home_link'),
    path('consultoria-vendas/', ConsultoriaVendasListView.as_view(), name='consultoria-vendas'),
    path('consultoria-vendas/calculo-piso-elevado/', calculo_piso_elevado, name='calculo-piso-elevado'),
    path('consultoria-vendas/calculo-quimicos/', calculo_quimicos, name='calculo-quimicos'),
    path('consultoria-vendas/calculo-niveladores/', calculo_niveladores, name='calculo-niveladores'),
]
