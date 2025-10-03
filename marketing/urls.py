from django.urls import path
from home.views import IndexListView

app_name = 'marketing'

urlpatterns = [
    path('', IndexListView.as_view(), name='marketing'),
]
