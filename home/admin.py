from django.contrib import admin
from django.http import HttpRequest
from home.models import (HomeLinks, SiteSetup, HomeLinksDocumentos, AssistentesTecnicos, AssistentesTecnicosAgenda,
                         Jobs, Paises, Estados, Cidades, Bancos)
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

    # override do get_inlines para não mostrar na inclusão
    def get_inlines(self, request, obj):
        if obj:
            return super().get_inlines(request, obj)
        return []


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
    list_display = 'id', 'data_as_ddmmyyyy', 'data_dia_semana', 'assistente_tecnico', 'agenda',
    list_display_links = 'data_as_ddmmyyyy', 'assistente_tecnico', 'agenda',
    ordering = '-data', 'assistente_tecnico',
    list_filter = 'assistente_tecnico',


@admin.register(Jobs)
class JobsAdmin(admin.ModelAdmin):
    list_display = 'id', 'descricao', 'status',
    list_display_links = 'id', 'descricao', 'status',
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Paises)
class PaisesAdmin(admin.ModelAdmin):
    list_display = 'id', 'nome',
    list_display_links = 'id', 'nome',
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'chave_migracao',


@admin.register(Estados)
class EstadosAdmin(admin.ModelAdmin):
    list_display = 'id', 'uf', 'sigla',
    list_display_links = 'id', 'uf', 'sigla',
    ordering = 'uf',
    search_fields = 'uf', 'sigla',
    readonly_fields = 'chave_migracao',


@admin.register(Cidades)
class CidadesAdmin(admin.ModelAdmin):
    list_display = 'id', 'nome', 'estado',
    list_display_links = 'id', 'estado', 'nome',
    ordering = 'nome',
    search_fields = 'nome', 'estado__uf',
    readonly_fields = 'chave_migracao',


@admin.register(Bancos)
class BancosAdmin(admin.ModelAdmin):
    list_display = 'id', 'nome',
    list_display_links = 'id', 'nome',
    ordering = 'nome',
    search_fields = 'nome',
