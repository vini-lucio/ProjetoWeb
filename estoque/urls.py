from django.urls import path
from .views import estoque

app_name = 'estoque'

urlpatterns = [
    path('', estoque, name='estoque'),
]
