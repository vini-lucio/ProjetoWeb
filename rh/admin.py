from typing import Any
from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from rh.models import Cbo, Dissidios, Escolaridades, TransporteLinhas, TransporteTipos, DependentesTipos


@admin.register(Cbo)
class CboAdmin(admin.ModelAdmin):
    list_display = 'id', 'numero', 'descricao',
    list_display_links = 'id', 'numero', 'descricao',
    ordering = 'descricao',
    search_fields = 'numero', 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Dissidios)
class DissidiosAdmin(admin.ModelAdmin):
    list_display = 'id', 'job', 'data_as_ddmmyyyy', 'dissidio_total', 'aplicado',
    list_display_links = 'id', 'job', 'data_as_ddmmyyyy', 'dissidio_total',
    ordering = '-data', 'job',
    list_filter = 'job',
    readonly_fields = ('dissidio_total', 'chave_migracao', 'aplicado', 'criado_por', 'criado_em', 'atualizado_por',
                       'atualizado_em',)

    def save_model(self, request: HttpRequest, obj: Any, form: ModelForm, change: bool) -> None:
        if not obj.pk:
            obj.criado_por = request.user
            obj.atualizado_por = request.user
        if change:
            obj.atualizado_por = request.user
        obj.save()
        return super().save_model(request, obj, form, change)


@admin.register(Escolaridades)
class EscolaridadesAdmin(admin.ModelAdmin):
    list_display = 'id', 'descricao',
    list_display_links = 'id', 'descricao',
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(TransporteLinhas)
class TransporteLinhasAdmin(admin.ModelAdmin):
    list_display = 'id', 'descricao',
    list_display_links = 'id', 'descricao',
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(TransporteTipos)
class TransporteTiposAdmin(admin.ModelAdmin):
    list_display = 'id', 'descricao',
    list_display_links = 'id', 'descricao',
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(DependentesTipos)
class DependentesTiposAdmin(admin.ModelAdmin):
    list_display = 'id', 'descricao',
    list_display_links = 'id', 'descricao',
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',
