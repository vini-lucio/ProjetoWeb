from django.contrib import admin
from .models import LeadsRdStation
from utils.base_models import BaseModelAdminRedRequired


@admin.register(LeadsRdStation)
class LeadsRdStationAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'chave_analysis', 'empresa', 'nome', 'lead_valido',
    list_display_links = list_display
    search_fields = 'chave_analysis', 'empresa', 'nome',
    readonly_fields = 'dados_bruto',

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)

        if obj:
            return campos

        campos = list(campos)
        campos.remove('dados_bruto')
        return campos
