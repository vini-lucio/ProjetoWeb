from django.contrib import admin
from rh_relatorios.models import Admissoes, Aniversariantes, Filhos12Anos
from utils.base_models import BaseViewAdmin, ExportarXlsxMixIn


@admin.register(Admissoes)
class AdmissõesAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'registro', 'nome', 'mes_entrada', 'data_entrada_as_ddmmyyyy', 'tempo_casa_anos',
    list_display_links = list_display
    list_filter = 'job', 'mes_entrada',
    ordering = 'job', 'nome',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = 'job', 'registro', 'nome', 'mes_entrada', 'data_entrada', 'tempo_casa_anos',


@admin.register(Aniversariantes)
class AniversariantesAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'nome', 'mes_nascimento', 'data_nascimento_as_ddmmyyyy',
    list_display_links = list_display
    list_filter = 'job', 'mes_nascimento',
    ordering = 'job', 'nome',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = 'job', 'nome', 'mes_nascimento', 'data_nascimento',


@admin.register(Filhos12Anos)
class Filhos12AnosAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'nome', 'nome_dependente', 'data_nascimento_as_ddmmyyyy', 'idade',
    list_display_links = list_display
    list_filter = 'job',
    ordering = 'job', 'nome', '-idade',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = 'job', 'nome', 'nome_dependente', 'data_nascimento', 'idade',
