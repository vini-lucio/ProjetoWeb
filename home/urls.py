from django.urls import path
from home.views import IndexListView, HomeLinkDetailView, ConsultoriaVendasListView

app_name = 'home'

urlpatterns = [
    path('', IndexListView.as_view(), name='index'),
    path('home_link/<slug:slug>/', HomeLinkDetailView.as_view(), name='home_link'),
    path('consultoria-vendas/', ConsultoriaVendasListView.as_view(), name='consultoria-vendas'),
]
