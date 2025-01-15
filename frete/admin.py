from django.contrib import admin
from frete.models import Transportadoras, TransportadorasOrigemDestino
from utils.base_models import BaseModelAdminRedRequiredLog


@admin.register(Transportadoras)
class TransportadorasAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'nome', 'status', 'simples_nacional', 'entrega_uf_diferente_faturamento',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'chave_migracao',


@admin.register(TransportadorasOrigemDestino)
class TransportadorasOrigemDestinoAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'transportadora', 'estado_origem_destino',
    list_display_links = list_display
    ordering = 'transportadora', 'estado_origem_destino',
    search_fields = 'transportadora__nome',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'estado_origem_destino',
