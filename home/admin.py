from django.contrib import admin
from django.http import HttpRequest
from home.models import HomeLinks, SiteSetup, HomeLinksDocumentos, AssistentesTecnicos, AssistentesTecnicosAgenda
from django_summernote.admin import SummernoteModelAdmin


class HomeLinksDocumentosInLine(admin.TabularInline):
    model = HomeLinksDocumentos
    extra = 1
    verbose_name = "Documento do Home Link"
    verbose_name_plural = "Documentos do Home Link"


@admin.register(HomeLinks)
class HomeLinksAdmin(SummernoteModelAdmin):
    # class HomeLinksAdmin(admin.ModelAdmin):
    summernote_fields = 'conteudo',
    list_display = 'id', 'titulo', 'tamanho_botao', 'ordem', 'visivel',
    list_display_links = 'titulo',
    list_editable = 'visivel', 'ordem'
    readonly_fields = 'slug',
    ordering = 'tamanho_botao', 'ordem', 'id',
    search_fields = 'tamanho_botao', 'titulo',
    inlines = HomeLinksDocumentosInLine,


@admin.register(SiteSetup)
class SiteSetupAdmin(admin.ModelAdmin):
    readonly_fields = 'meta_diaria',

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSetup.objects.exists()


@admin.register(AssistentesTecnicos)
class AssistentesTecnicosAdmin(admin.ModelAdmin):
    list_display = 'id', 'nome', 'status',
    list_display_links = 'nome',
    list_editable = 'status',
    ordering = 'nome',
    search_fields = 'nome',


@admin.register(AssistentesTecnicosAgenda)
class AssistentesTecnicosAgendaAdmin(admin.ModelAdmin):
    list_display = 'id', 'data', 'data_dia_semana', 'assistente_tecnico',
    list_display_links = 'data', 'assistente_tecnico',
    ordering = '-data', 'assistente_tecnico',
    list_filter = 'assistente_tecnico',
