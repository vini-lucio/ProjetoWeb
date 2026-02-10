from django.contrib import admin
from .models import OC_MP_ITENS
from utils.base_models import BaseViewAdmin


@admin.register(OC_MP_ITENS)
class OC_MP_ITENS_Admin(BaseViewAdmin, admin.ModelAdmin):
    list_display = 'CHAVE_OC', 'data_entrega_as_ddmmyyyy', 'CHAVE_MATERIAL', 'QUANTIDADE', 'CHAVE_UNIDADE',
    list_display_links = list_display
    search_fields = 'CHAVE_OC__CHAVE',
    ordering = '-DATA_ENTREGA',

    class Media:
        css = {'all': ('admin/css/tablet.css',)}
