from django.urls import path
from frete.views import calculo_frete, prazos

app_name = 'frete'

urlpatterns = [
    path('', calculo_frete, name='calculo-frete'),
    path('prazos/', prazos, name='prazos'),
]
