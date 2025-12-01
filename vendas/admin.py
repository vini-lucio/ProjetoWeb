from django.contrib import admin
from utils.base_models import BaseModelAdminRedRequiredLog, BaseModelAdminRedRequired
from .models import RncNotas, MotivosRnc


@admin.register(MotivosRnc)
class MotivosRncAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',


@admin.register(RncNotas)
class RncNotasAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'job__descricao', 'nota_fiscal', 'cliente', 'responsavel__nome'
    list_display_links = list_display
    ordering = '-pk',
    search_fields = 'nota_fiscal',
    readonly_fields = ['criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'cliente',
                       'descricao_cancelamento']

    fieldsets = (
        (None, {
            "fields": (
                'job', 'nota_fiscal', 'data', 'responsavel',
            ),
        }),
        ('Detalhes', {
            "fields": (
                'cliente', 'origem', 'motivo', 'descricao_cancelamento', 'descricao', 'acao_imediata',
            ),
        }),
        ('Resolução', {
            "fields": (
                'custo_adicional', 'custo_recuperado', 'follow_up',
            ),
        }),
        ('Logs', {
            "fields": (
                'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
            ),
        }),
    )
