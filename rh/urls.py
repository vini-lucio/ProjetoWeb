from django.urls import path
from home.views import IndexListView

app_name = 'rh'

urlpatterns = [
    path('', IndexListView.as_view(), name='index'),
]
