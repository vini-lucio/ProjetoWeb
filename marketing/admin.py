from django.contrib import admin
from .models import LeadsRdStation
from utils.base_models import BaseModelAdminRedRequired, ExportarXlsxMixIn

# TODO: Documentar


@admin.register(LeadsRdStation)
class LeadsRdStationAdmin(ExportarXlsxMixIn, BaseModelAdminRedRequired):
    list_display = ('id', 'criado_em_as_ddmmyyyy', 'chave_analysis', 'empresa', 'identificador', 'nome',
                    'responsavel__nome', 'lead_valido',)
    list_display_links = list_display
    search_fields = 'chave_analysis', 'empresa', 'nome', 'identificador', 'responsavel__nome',
    readonly_fields = 'dados_bruto',
    autocomplete_fields = 'responsavel',

    actions = 'exportar_excel',
    campos_exportar = ['cnpj', 'empresa', 'nome', 'telefone', 'email_lead', 'origem', 'responsavel_nome']

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)

        if obj:
            return campos

        campos = list(campos)
        campos.remove('dados_bruto')
        return campos
