from django.contrib import admin
from frete.models import (Transportadoras, TransportadorasOrigemDestino, TransportadorasRegioesValores,
                          TransportadorasRegioesMargens, TransportadorasRegioesCidades)
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
    list_display = 'id', 'transportadora', 'estado_origem_destino', 'status',
    list_display_links = list_display
    ordering = 'transportadora', 'estado_origem_destino',
    search_fields = 'transportadora__nome',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'estado_origem_destino',


class TransportadorasRegioesMargensInLine(admin.TabularInline):
    model = TransportadorasRegioesMargens
    extra = 1
    verbose_name = "Transportadora Região Margem"
    verbose_name_plural = "Transportadora Região Margens"
    ordering = 'ate_kg',
    fields = 'ate_kg', 'valor',


@admin.register(TransportadorasRegioesValores)
class TransportadorasRegioesValoresAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'transportadora_origem_destino', 'descricao', 'status',
    list_display_links = list_display
    ordering = 'transportadora_origem_destino', 'descricao',
    search_fields = 'transportadora_origem_destino__transportadora__nome',
    readonly_fields = ['arquivo_migrar_cidades', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',]
    autocomplete_fields = 'transportadora_origem_destino',
    inlines = TransportadorasRegioesMargensInLine,

    fieldsets = (
        (None, {
            "fields": (
                'transportadora_origem_destino', 'descricao', 'status', 'razao', 'observacoes',
                'atendimento_cidades_especificas', 'arquivo_migrar_cidades',
            ),
        }),
        ('Prazo Padrão', {
            "fields": (
                'prazo_tipo', 'prazo_padrao', 'frequencia_padrao', 'observacoes_prazo_padrao',
            ),
        }),
        ('Valor kg', {
            "fields": (
                'valor_kg', 'valor_kg_excedente',
            ),
        }),
        ('Advaloren / Frete Valor', {
            "fields": (
                'advaloren', 'advaloren_valor_minimo',
            ),
        }),
        ('Gris / Gerenciamento de Risco', {
            "fields": (
                'gris', 'gris_valor_minimo',
            ),
        }),
        ('Taxas', {
            "fields": (
                'taxa_coleta', 'taxa_conhecimento', 'taxa_sefaz', 'taxa_suframa',
            ),
        }),
        ('Pedagio', {
            "fields": (
                'pedagio_fracao', 'pedagio_valor_fracao', 'pedagio_valor_minimo',
            ),
        }),
        ('Outras Taxas (Frete Peso)', {
            "fields": (
                'taxa_frete_peso', 'taxa_frete_peso_valor_minimo',
            ),
        }),
        ('Outras Taxas (Valor da Nota)', {
            "fields": (
                'taxa_valor_nota', 'taxa_valor_nota_valor_minimo',
            ),
        }),
        ('Frete Minimo', {
            "fields": (
                'frete_minimo_valor', 'frete_minimo_percentual',
            ),
        }),
        ('Zona Rural', {
            "fields": (
                'atendimento_zona_rural', 'taxa_zona_rural',
            ),
        }),
        ('Logs', {
            "fields": (
                'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
            ),
        }),
    )

    def get_inlines(self, request, obj):
        if obj:
            return super().get_inlines(request, obj)
        return []

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)

        if not obj:
            return campos

        campos = list(campos)
        campos.remove('arquivo_migrar_cidades')
        return campos


@admin.register(TransportadorasRegioesMargens)
class TransportadorasRegioesMargensAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'transportadora_regiao_valor', 'ate_kg', 'valor',
    list_display_links = list_display
    ordering = 'transportadora_regiao_valor', 'ate_kg',
    search_fields = 'transportadora_regiao_valor__transportadora_origem_destino__transportadora__nome',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'transportadora_regiao_valor',


@admin.register(TransportadorasRegioesCidades)
class TransportadorasRegioesCidadesAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'transportadora_regiao_valor', 'cidade', 'prazo', 'prazo_tipo', 'cif',
    list_display_links = list_display
    ordering = 'transportadora_regiao_valor', 'cidade',
    search_fields = ('transportadora_regiao_valor__transportadora_origem_destino__transportadora__nome',
                     'cidade__nome')
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'transportadora_regiao_valor', 'cidade',
