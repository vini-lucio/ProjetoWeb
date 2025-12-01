from django.urls import path
from home.views import IndexListView

app_name = 'vendas'

urlpatterns = [
    path('', IndexListView.as_view(), name='vendas'),
]
