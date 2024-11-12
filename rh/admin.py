from django.contrib import admin
from rh.models import (Cbo, Dissidios, Escolaridades, TransporteLinhas, TransporteTipos, DependentesTipos, Setores,
                       Funcoes, Horarios, Funcionarios, Afastamentos, Dependentes)
from utils.base_models import BaseModelAdminRedRequiredLog, BaseModelAdminRedRequired


@admin.register(Cbo)
class CboAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'numero', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'numero', 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Dissidios)
class DissidiosAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'job', 'data_as_ddmmyyyy', 'dissidio_total', 'aplicado',
    list_display_links = 'id', 'job', 'data_as_ddmmyyyy', 'dissidio_total',
    ordering = '-data', 'job',
    list_filter = 'job',
    readonly_fields = ('dissidio_total', 'chave_migracao', 'aplicado', 'criado_por', 'criado_em', 'atualizado_por',
                       'atualizado_em',)


@admin.register(Escolaridades)
class EscolaridadesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(TransporteLinhas)
class TransporteLinhasAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(TransporteTipos)
class TransporteTiposAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(DependentesTipos)
class DependentesTiposAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Setores)
class SetoresAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao', 'plano_contas',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Funcoes)
class FuncoesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Horarios)
class HorariosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'horario_inicio_fim_sexta', 'intervalo_inicio_fim',
    list_display_links = list_display
    ordering = 'inicio', 'intervalo_inicio', 'intervalo_fim', 'fim', 'sexta_fim'
    search_fields = 'horario',
    readonly_fields = 'chave_migracao',


@admin.register(Funcionarios)
class FuncionariosAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'job', 'registro', 'nome', 'status',
    list_display_links = list_display
    ordering = 'nome',
    list_filter = 'job', 'data_saida',
    search_fields = 'nome',
    readonly_fields = 'image_tag', 'status', 'chave_migracao', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = ('job', 'cidade', 'uf', 'pais', 'cidade_nascimento', 'uf_nascimento', 'pais_nascimento',
                           'escolaridade', 'banco')
    fieldsets = (
        (None, {
            'fields': (
                'job', 'registro', 'foto', 'image_tag', 'nome',
            ),
        }),
        ('Datas', {
            'fields': (
                'data_entrada', 'data_saida', 'data_inicio_experiencia', 'data_fim_experiencia',
                'data_inicio_prorrogacao', 'data_fim_prorrogacao', 'status',
            ),
        }),
        ('Endereço', {
            'fields': (
                'endereco', 'numero', 'complemento', 'cep', 'bairro', 'cidade', 'uf', 'pais',
            ),
        }),
        ('Dados Pessoais', {
            'fields': (
                'data_nascimento', 'cidade_nascimento', 'uf_nascimento', 'pais_nascimento', 'sexo', 'estado_civil',
                'escolaridade', 'escolaridade_status', 'data_ultimo_exame', 'exame_tipo', 'exame_observacoes',
            ),
        }),
        ('Contato', {
            'fields': (
                'fone_1', 'fone_2', 'fone_recado', 'email',
            ),
        }),
        ('Documentos', {
            'fields': (
                'rg', 'rg_orgao_emissor', 'cpf', 'pis', 'carteira_profissional', 'carteira_profissional_serie',
                'titulo_eleitoral', 'titulo_eleitoral_zona', 'titulo_eleitoral_sessao', 'certificado_militar', 'cnh',
                'cnh_categoria', 'cnh_data_emissao', 'cnh_data_vencimento', 'certidao_tipo', 'certidao_data_emissao',
                'certidao_termo_matricula', 'certidao_livro', 'certidao_folha',
            ),
        }),
        ('Financeiro', {
            'fields': (
                'banco', 'agencia', 'conta', 'conta_tipo',
            ),
        }),
        ('Observações', {
            'fields': (
                'observacoes_gerais',
            ),
        }),
        ('Logs', {
            'fields': (
                'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'chave_migracao',
            ),
        }),
    )


@admin.register(Afastamentos)
class AfastamentosAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'funcionario', 'data_afastamento_as_ddmmyyyy', 'data_retorno_as_ddmmyyyy', 'motivo',
    list_display_links = list_display
    ordering = '-id',
    list_filter = 'data_retorno',
    search_fields = 'funcionario__nome',
    readonly_fields = 'chave_migracao', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'funcionario',


@admin.register(Dependentes)
class DependentesAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'funcionario', 'nome', 'dependente_tipo',
    list_display_links = list_display
    ordering = 'funcionario', 'nome',
    search_fields = 'funcionario__nome', 'nome',
    readonly_fields = 'chave_migracao', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'funcionario',
