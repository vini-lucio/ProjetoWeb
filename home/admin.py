from django.contrib import admin
from home.models import HomeLinks


@admin.register(HomeLinks)
class HomeLinksAdmin(admin.ModelAdmin):
    list_display = 'id', 'titulo', 'tamanho_botao', 'ordem', 'visivel',
    list_display_links = 'titulo',
    list_editable = 'visivel', 'ordem'
    readonly_fields = 'slug',
    ordering = 'tamanho_botao', 'ordem', 'id',
