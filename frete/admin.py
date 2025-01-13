from django.contrib import admin
from frete.models import Transportadoras
from utils.base_models import BaseModelAdminRedRequiredLog


@admin.register(Transportadoras)
class TransportadorasAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'nome', 'status', 'simples_nacional', 'entrega_uf_diferente_faturamento',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'chave_migracao',
