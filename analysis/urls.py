from django.urls import path
from analysis.views import GruposEconomicosDetailView

app_name = 'analysis'

urlpatterns = [
    path('grupo-economico/<int:pk>/', GruposEconomicosDetailView.as_view(), name='grupo-economico'),
]
