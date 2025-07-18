from django.contrib import admin
from dashboards.models import Indicadores, IndicadoresValores, MetasCarteiras, IndicadoresPeriodos
from utils.base_models import BaseModelAdminRedRequired


@admin.register(Indicadores)
class IndicadoresAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',


@admin.register(IndicadoresPeriodos)
class IndicadoresPeriodosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'ano_referencia', 'mes_referencia',
    list_display_links = list_display
    ordering = '-ano_referencia', '-mes_referencia',


@admin.register(IndicadoresValores)
class IndicadoresValoresAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'indicador', 'periodo', 'valor_meta', 'valor_real',
    list_display_links = list_display
    ordering = '-periodo__ano_referencia', '-periodo__mes_referencia', 'indicador'
    search_fields = 'indicador__descricao',


@admin.register(MetasCarteiras)
class MetasCarteirasAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'indicador_valor', 'vendedor', 'responsavel', 'valor_meta', 'valor_real', 'considerar_total',
    list_display_links = list_display
    ordering = '-pk',
    search_fields = 'vendedor__nome',
    autocomplete_fields = 'responsavel',
    readonly_fields = 'indicador_valor',

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)

        if obj:
            return campos

        campos = list(campos)
        campos.remove('indicador_valor')
        return campos

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
