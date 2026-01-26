from django.urls import path
from .views import estoque, estoque_alterar, estoque_mover

app_name = 'estoque'

urlpatterns = [
    path('', estoque, name='estoque'),
    path('alterar/<int:pk>/', estoque_alterar, name='alterar'),
    path('mover/<int:pk>/', estoque_mover, name='mover'),
]
