from django.urls import path
from frete.views import calculo_frete

app_name = 'frete'

urlpatterns = [
    path('', calculo_frete, name='calculo-frete'),
]
