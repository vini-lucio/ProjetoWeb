from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import LeadsRdStation
from analysis.models import CLIENTES
from utils.base_models import BaseModelAdminRedRequired, ExportarXlsxMixIn


@admin.register(LeadsRdStation)
class LeadsRdStationAdmin(ExportarXlsxMixIn, BaseModelAdminRedRequired):
    list_display = ('id', 'criado_em_as_ddmmyyyy', 'chave_analysis', 'empresa', 'identificador', 'nome',
                    'responsavel__nome', 'lead_valido',)
    list_display_links = list_display
    list_filter = [('chave_analysis', admin.EmptyFieldListFilter),]
    search_fields = 'chave_analysis', 'empresa', 'nome', 'identificador', 'responsavel__nome',
    readonly_fields = 'dados_bruto',
    autocomplete_fields = 'responsavel',

    actions = 'exportar_excel', 'preencher_chave_analysis',
    campos_exportar = ['cnpj', 'empresa', 'nome', 'telefone', 'email_lead', 'origem', 'responsavel_nome']

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)

        if obj:
            return campos

        campos = list(campos)
        campos.remove('dados_bruto')
        return campos

    def preencher_chave_analysis(self, request, queryset):
        """Ação para preencher automaticamente o campo chave_analysis se já houver cadastro no sistema Analysis."""
        for obj in queryset:
            if obj.chave_analysis:
                continue
            if not obj.cnpj:
                continue

            cliente = CLIENTES.get_cgc_digitos(obj.cnpj)
            if not cliente:
                continue

            obj.chave_analysis = cliente.pk
            try:
                obj.full_clean()
                obj.save()
            except ValidationError:
                # TODO: excluir ao inves de ignorar?
                continue

    preencher_chave_analysis.short_description = "Preencher ID Cliente Analysis selecionados"
