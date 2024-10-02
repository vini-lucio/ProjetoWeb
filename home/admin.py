from django.contrib import admin
from django.http import HttpRequest
from home.models import HomeLinks, SiteSetup
from django_summernote.admin import SummernoteModelAdmin


@admin.register(HomeLinks)
class HomeLinksAdmin(SummernoteModelAdmin):
    # class HomeLinksAdmin(admin.ModelAdmin):
    summernote_fields = 'conteudo',
    list_display = 'id', 'titulo', 'tamanho_botao', 'ordem', 'visivel',
    list_display_links = 'titulo',
    list_editable = 'visivel', 'ordem'
    readonly_fields = 'slug',
    ordering = 'tamanho_botao', 'ordem', 'id',
    search_fields = 'tamanho_botao',


@admin.register(SiteSetup)
class SiteSetupAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSetup.objects.exists()
