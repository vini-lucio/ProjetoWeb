# from django.shortcuts import render
from django.views.generic import ListView
from home.models import HomeLinks


# def index(request):
#     return render(request, 'home/pages/index.html')


class IndexListView(ListView):
    model = HomeLinks
    template_name = 'home/pages/index.html'
    context_object_name = 'home_links'
    ordering = 'tamanho_botao', 'ordem', 'id',
    queryset = HomeLinks.objects.filter(visivel=True)
