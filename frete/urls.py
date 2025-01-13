from django.urls import path
from home.views import IndexListView

app_name = 'frete'

urlpatterns = [
    path('', IndexListView.as_view(), name='index'),
]
