from django.urls import path
from home.views import IndexListView

app_name = 'estoque'

urlpatterns = [
    path('', IndexListView.as_view(), name='estoque'),
]
