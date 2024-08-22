from django.urls import path
from home.views import IndexListView

app_name = 'home'

urlpatterns = [
    path('', IndexListView.as_view(), name='index'),
]
