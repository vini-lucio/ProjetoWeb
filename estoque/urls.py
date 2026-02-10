from django.urls import path
from .views import estoque, estoque_alterar, estoque_mover, estoque_incluir_lote_mp

app_name = 'estoque'

urlpatterns = [
    path('', estoque, name='estoque'),
    path('alterar/<int:pk>/', estoque_alterar, name='alterar'),
    path('mover/<int:pk>/', estoque_mover, name='mover'),
    path('incluir-lote-mp/<int:pk>/', estoque_incluir_lote_mp, name='incluir-lote-mp'),
]
