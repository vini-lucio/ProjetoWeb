from django.contrib import admin
from django.http import HttpRequest
from .models import Enderecos, ProdutosPallets, Pallets
from utils.base_models import BaseModelAdminRedRequired


@admin.register(Enderecos)
class EnderecosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome', 'coluna', 'altura', 'tipo', 'tipo_produto', 'status',
    list_display_links = list_display
    search_fields = 'nome',
    readonly_fields = ['status',]

    def get_actions(self, request: HttpRequest):
        return []

    def get_readonly_fields(self, request: HttpRequest, obj):
        campos = super().get_readonly_fields(request, obj)
        if not obj:  # type:ignore
            return campos

        campos = list(campos) + ['nome', 'coluna', 'altura', 'tipo', 'tipo_produto', 'multi_pallet']
        return campos

    fieldsets = (
        (None, {
            "fields": (
                'nome', 'coluna', 'altura', 'tipo', 'multi_pallet', 'status',
            ),
        }),
        ('Produto', {
            "fields": (
                'tipo_produto', 'prioridade',
            ),
        }),
    )


@admin.register(Pallets)
class PalletsAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'endereco', 'quantidade_produtos',
    list_display_links = list_display
    readonly_fields = 'quantidade_produtos',

    def get_actions(self, request: HttpRequest):
        return []

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(ProdutosPallets)
class ProdutosPalletsAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'pallet', 'produto', 'quantidade', 'unidade', 'fornecedor', 'lote_fornecedor',
    list_display_links = list_display
    search_fields = 'produto__nome',
    readonly_fields = 'unidade',
    autocomplete_fields = 'fornecedor', 'produto',

    def get_actions(self, request: HttpRequest):
        return []

    def get_readonly_fields(self, request: HttpRequest, obj):
        campos = super().get_readonly_fields(request, obj)
        campos = list(campos)
        if obj:
            campos.append('produto')
            return campos
        campos.append('pallet')
        return campos

    fieldsets = (
        (None, {
            "fields": (
                'pallet',
            ),
        }),
        ('Produto', {
            "fields": (
                ('produto', 'quantidade', 'unidade'),
            ),
        }),
        ('Materia Prima', {
            "fields": (
                'fornecedor', 'lote_fornecedor',
            ),
        }),
    )

    class Media (BaseModelAdminRedRequired.Media):
        """Adiciona arquivo css ao herdado da classe pai"""
        css = {
            'all': BaseModelAdminRedRequired.Media.css['all'] + ('admin/css/tablet.css',)
        }
