from django.contrib import admin
from rh_relatorios.models import (Admissoes, Aniversariantes, Dependentes, FuncionariosListagem,
                                  FuncionariosSalarioFuncaoAtual, FuncionariosHistoricoSalarios,
                                  FuncionariosQuadroHorarios)
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


@admin.register(Dependentes)
class DependentesAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'nome', 'sexo', 'nome_dependente', 'data_nascimento_as_ddmmyyyy', 'idade', 'crianca',
    list_display_links = list_display
    list_filter = 'job', 'sexo', 'crianca',
    ordering = 'job', 'nome', '-idade',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = 'job', 'nome', 'sexo', 'nome_dependente', 'data_nascimento', 'idade', 'crianca',


@admin.register(FuncionariosListagem)
class FuncionariosListagemAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'nome', 'funcao', 'sexo', 'data_nascimento_as_ddmmyyyy', 'rg', 'membro_cipa',
    list_display_links = list_display
    list_filter = 'job', 'sexo', 'membro_cipa',
    ordering = 'job', 'nome',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = 'job', 'nome', 'funcao', 'sexo', 'data_nascimento', 'rg', 'membro_cipa',


@admin.register(FuncionariosSalarioFuncaoAtual)
class FuncionariosSalarioFuncaoAtualAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = ('job', 'nome', 'data_entrada_as_ddmmyyyy', 'setor', 'funcao', 'salario', 'salario_convertido',
                    'comissao_carteira', 'comissao_dupla', 'comissao_geral', )
    list_display_links = list_display
    list_filter = 'job',
    ordering = 'job', 'nome',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = ('job', 'nome', 'data_entrada', 'funcao', 'salario', 'salario_convertido', 'comissao_carteira',
                       'comissao_dupla', 'comissao_geral', )


@admin.register(FuncionariosHistoricoSalarios)
class FuncionariosHistoricoSalariosAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = ('job', 'nome', 'data_salario_as_ddmmyyyy', 'salario', 'salario_convertido', 'motivo',
                    'comissao_carteira', 'comissao_dupla', 'comissao_geral', )
    list_display_links = list_display
    list_filter = 'job', 'setor',
    ordering = 'job', 'nome', '-data_salario',
    search_fields = 'nome',
    fields = ('job', 'nome', 'data_entrada_as_ddmmyyyy', 'data_salario_as_ddmmyyyy', 'setor', 'funcao', 'motivo',
              'modalidade', 'salario', 'salario_convertido', 'comissao_carteira', 'comissao_dupla',
              'comissao_geral', 'observacoes',)
    actions = 'exportar_excel',

    campos_exportar = ('job', 'nome', 'data_entrada', 'data_salario', 'setor', 'funcao', 'motivo', 'modalidade',
                       'salario', 'salario_convertido', 'comissao_carteira', 'comissao_dupla', 'comissao_geral',
                       'observacoes',)


@admin.register(FuncionariosQuadroHorarios)
class FuncionariosQuadroHorariosAdmin(BaseViewAdmin, ExportarXlsxMixIn):
    list_display = 'job', 'registro', 'nome', 'carteira_profissional', 'setor', 'funcao', 'horario', 'almoco',
    list_display_links = list_display
    list_filter = 'job',
    ordering = 'job', 'nome',
    search_fields = 'nome',
    fields = list_display
    actions = 'exportar_excel',

    campos_exportar = list_display
