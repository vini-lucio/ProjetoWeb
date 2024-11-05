from django.contrib import admin
from rh.models import Cbo


@admin.register(Cbo)
class CboAdmin(admin.ModelAdmin):
    list_display = 'id', 'numero', 'descricao',
    list_display_links = 'id', 'numero', 'descricao',
    ordering = 'descricao',
    search_fields = 'numero', 'descricao',
    readonly_fields = 'chave_migracao',
