from django.contrib import admin
from django.db.models import Value
from django.db.models.query import QuerySet
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse
from home.models import (HomeLinks, SiteSetup, HomeLinksDocumentos, AssistentesTecnicos, AssistentesTecnicosAgenda,
                         Jobs, Paises, Estados, Cidades, Bancos, Atualizacoes, ProdutosModelos, ProdutosModelosTopicos,
                         ProdutosModelosTags, Unidades, Produtos, EstadosIcms, Vendedores, CanaisVendas, Regioes,
                         VendedoresRegioes, VendedoresEstados, ControleInscricoesEstaduais, InscricoesEstaduais)
from django_summernote.admin import SummernoteModelAdmin
from utils.base_models import (BaseModelAdminRedRequired, BaseModelAdminRedRequiredLog, AdminRedRequiredMixIn,
                               AdminLogMixIn, ExportarXlsxMixIn)
from utils.exportar_excel import arquivo_excel
import os
import zipfile
import tempfile
import importlib


class HomeLinksDocumentosInLine(admin.TabularInline):
    model = HomeLinksDocumentos
    extra = 1
    verbose_name = "Documento do Home Link"
    verbose_name_plural = "Documentos do Home Link"


@admin.register(HomeLinks)
class HomeLinksAdmin(AdminRedRequiredMixIn, SummernoteModelAdmin):
    # class HomeLinksAdmin(admin.ModelAdmin):
    summernote_fields = 'conteudo',
    list_display = 'id', 'titulo', 'tamanho_botao', 'ordem', 'visivel',
    list_display_links = 'titulo',
    list_editable = 'visivel', 'ordem'
    readonly_fields = 'slug',
    ordering = 'tamanho_botao', 'ordem', 'id',
    search_fields = 'tamanho_botao', 'titulo',
    inlines = HomeLinksDocumentosInLine,

    # override do get_inlines para não mostrar na inclusão
    def get_inlines(self, request, obj):
        if obj:
            return super().get_inlines(request, obj)
        return []


@admin.register(SiteSetup)
class SiteSetupAdmin(BaseModelAdminRedRequired):
    readonly_fields = 'meta_diaria',

    fieldsets = (
        ('Dados Site', {
            "fields": (
                'favicon', 'logo_cabecalho', 'texto_rodape',
            ),
        }),
        ('Dados Mês', {
            "fields": (
                'primeiro_dia_mes', 'primeiro_dia_util_mes', 'ultimo_dia_mes', 'primeiro_dia_util_proximo_mes',
                'despesa_administrativa_fixa',
            ),
        }),
        ('Meta Mês', {
            "fields": (
                'meta_mes', 'dias_uteis_mes', 'dias_uteis_mes_reais', 'meta_diaria',
            ),
        }),
        ('Meta Rentabilidade', {
            "fields": (
                'rentabilidade_verde', 'rentabilidade_amarela', 'rentabilidade_vermelha',
            ),
        }),
        ('Atualizações Dados Ano', {
            "fields": (
                'atualizacoes_ano', 'atualizacoes_ano_inicio', 'atualizacoes_ano_fim', 'atualizacoes_data_ano_inicio',
                'atualizacoes_data_ano_fim',
            ),
        }),
        ('Atualizações Dados Mês', {
            "fields": (
                'atualizacoes_mes', 'atualizacoes_data_mes_inicio', 'atualizacoes_data_mes_fim',
            ),
        }),
        ('Volume Frete Padrão', {
            "fields": (
                'medida_volume_padrao_x', 'medida_volume_padrao_y', 'medida_volume_padrao_z',
            ),
        }),
        ('Impostos Calulo de Frete', {
            "fields": (
                'aliquota_pis_cofins', 'aliquota_icms_simples',
            ),
        }),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSetup.objects.exists()


@admin.register(AssistentesTecnicos)
class AssistentesTecnicosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome', 'status',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',


@admin.register(AssistentesTecnicosAgenda)
class AssistentesTecnicosAgendaAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'data_as_ddmmyyyy', 'data_dia_semana', 'assistente_tecnico', 'agenda',
    list_display_links = list_display
    ordering = '-data', 'assistente_tecnico',
    list_filter = 'assistente_tecnico',


@admin.register(Jobs)
class JobsAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao', 'despesa_administrativa_fixa', 'status',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'chave_migracao',


@admin.register(Paises)
class PaisesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'chave_migracao',


@admin.register(Regioes)
class RegioesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',


class EstadosIcmsInLine(admin.TabularInline):
    model = EstadosIcms
    extra = 1
    verbose_name = "Estado ICMS"
    verbose_name_plural = "Estados ICMS"
    fk_name = 'uf_origem'
    ordering = 'uf_origem__sigla', 'uf_destino__sigla',


@admin.register(Estados)
class EstadosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'uf', 'sigla',
    list_display_links = list_display
    ordering = 'uf',
    search_fields = 'uf', 'sigla',
    readonly_fields = 'chave_migracao',
    inlines = EstadosIcmsInLine,

    def get_inlines(self, request, obj):
        if obj:
            return super().get_inlines(request, obj)
        return []


@admin.register(EstadosIcms)
class EstadosIcmsAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'uf_origem', 'uf_destino', 'icms', 'icms_frete',
    list_display_links = list_display
    ordering = 'uf_origem__sigla', 'uf_destino__sigla',
    search_fields = 'uf_origem__sigla', 'uf_destino__sigla', 'origem_destino',

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(origem_destino=Concat('uf_origem__sigla', Value('-'), 'uf_destino__sigla'))
        return queryset


@admin.register(Cidades)
class CidadesAdmin(ExportarXlsxMixIn, BaseModelAdminRedRequired):
    list_display = 'id', 'nome', 'estado',
    list_display_links = list_display
    list_filter = 'estado',
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'chave_migracao',
    actions = 'exportar_excel',
    campos_exportar = ['nome', 'estado_sigla',]


@admin.register(Bancos)
class BancosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',


@admin.register(Atualizacoes)
class AtualizacoesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'app', 'arquivo', 'descricao', 'gera_arquivo',
    list_display_links = list_display
    list_filter = 'gera_arquivo',
    ordering = 'descricao',
    search_fields = 'descricao', 'app', 'arquivo',
    actions = 'exportar_atualizacoes', 'executar_funcoes',

    campos_exportar = ['descricao', 'nome_funcao']

    @admin.action(description="Exportar .XLSX Selecionados .ZIP")
    def exportar_atualizacoes(self, request, queryset):
        # campos_exportar = [field for field in self.campos_exportar]

        with tempfile.TemporaryDirectory() as pasta_temporaria:
            caminhos_arquivos_compactar = []

            for obj in queryset:
                if obj.gera_arquivo:
                    nome_arquivo_exportar = obj.nome_funcao
                    modulo = importlib.import_module(f'{obj.app}.{obj.arquivo}')
                    funcao = getattr(modulo, nome_arquivo_exportar)
                    resultado = funcao()

                    cabecalho = [cabecalho for cabecalho in resultado[0].keys()]

                    conteudo = []
                    for registro in resultado:
                        linha = [valor for chave, valor in registro.items()]
                        conteudo.append(linha)

                    workbook = arquivo_excel(conteudo, cabecalho)

                    caminho_arquivo_excel = os.path.join(pasta_temporaria, f'{nome_arquivo_exportar}.xlsx')
                    workbook.save(caminho_arquivo_excel)  # type:ignore
                    caminhos_arquivos_compactar.append(caminho_arquivo_excel)

            caminho_arquivo_zip = os.path.join(pasta_temporaria, 'atualizacoes.zip')
            with zipfile.ZipFile(caminho_arquivo_zip, 'w') as arquivo_zip:
                for caminho_arquivo_compactar in caminhos_arquivos_compactar:
                    arquivo_zip.write(caminho_arquivo_compactar, os.path.basename(caminho_arquivo_compactar))

            with open(caminho_arquivo_zip, 'rb') as arquivo_zip:
                response = HttpResponse(arquivo_zip.read(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename=atualizacoes.zip'

        return response

    @admin.action(description="Executar funções selecionadas")
    def executar_funcoes(self, request, queryset):
        for obj in queryset:
            modulo = importlib.import_module(f'{obj.app}.{obj.arquivo}')
            funcao = getattr(modulo, obj.nome_funcao)
            if obj.arquivo == 'tasks':
                funcao.now()
            else:
                funcao()


@admin.register(ProdutosModelos)
class ProdutosModelosAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao', 'tags__descricao',
    readonly_fields = 'slug', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'tags',


@admin.register(ProdutosModelosTopicos)
class ProdutosModelosTopicosAdmin(AdminRedRequiredMixIn, AdminLogMixIn, SummernoteModelAdmin):
    summernote_fields = 'conteudo',
    list_display = 'id', 'modelo', 'titulo', 'ordem',
    list_display_links = 'id', 'modelo', 'titulo',
    list_editable = 'ordem',
    ordering = 'modelo__descricao', 'ordem', 'titulo',
    search_fields = 'modelo__descricao', 'titulo',
    readonly_fields = 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
    autocomplete_fields = 'modelo',


@admin.register(ProdutosModelosTags)
class ProdutosModelosTagsAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    readonly_fields = 'slug',


@admin.register(Unidades)
class UnidadesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'unidade', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'unidade', 'descricao',


@admin.register(Produtos)
class ProdutosAdmin(BaseModelAdminRedRequiredLog):
    list_display = 'id', 'nome', 'm3_volume', 'status',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = []
    autocomplete_fields = 'modelo',

    def get_readonly_fields(self, request, obj):
        campos = super().get_readonly_fields(request, obj)
        campos = ['m3_volume', 'chave_migracao', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',]
        if obj:
            if obj.medida_volume_padrao:
                campos = ['m3_volume', 'chave_migracao', 'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em',
                          'medida_volume_x', 'medida_volume_y', 'medida_volume_z',]
        return campos

    fieldsets = (
        (None, {
            "fields": (
                'chave_analysis', 'modelo', 'nome', 'unidade', 'descricao', 'peso_liquido', 'peso_bruto', 'status',
            ),
        }),
        ('Embalagem', {
            "fields": (
                'multiplicidade', 'tipo_embalagem', 'medida_embalagem_x', 'medida_embalagem_y', 'ean13',
            ),
        }),
        ('Volume Frete', {
            "fields": (
                'quantidade_volume', 'medida_volume_padrao', 'medida_volume_x', 'medida_volume_y', 'medida_volume_z',
                'm3_volume',
            ),
        }),
        ('Produção', {
            "fields": (
                'aditivo_percentual',
            ),
        }),
        ('Estoque', {
            "fields": (
                'prioridade',
            ),
        }),
        ('Logs', {
            "fields": (
                'criado_por', 'criado_em', 'atualizado_por', 'atualizado_em', 'chave_migracao',
            ),
        }),
    )


@admin.register(CanaisVendas)
class CanaisVendasAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',


class VendedoresRegioesInLine(admin.TabularInline):
    model = VendedoresRegioes
    extra = 1
    verbose_name = "Vendedor Região"
    verbose_name_plural = "Vendedor Regiões"
    ordering = 'regiao__nome',
    autocomplete_fields = 'regiao',


class VendedoresEstadosInLine(admin.TabularInline):
    model = VendedoresEstados
    extra = 1
    verbose_name = "Vendedor Estado"
    verbose_name_plural = "Vendedor Estados"
    ordering = 'estado__uf',
    autocomplete_fields = 'estado',


@admin.register(Vendedores)
class VendedoresAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome', 'meta_mes', 'considerar_total', 'status',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    inlines = VendedoresRegioesInLine, VendedoresEstadosInLine,
    autocomplete_fields = 'responsavel',

    def get_inlines(self, request, obj):
        if obj:
            if obj.status == 'ativo':
                return super().get_inlines(request, obj)
        return []


@admin.register(ControleInscricoesEstaduais)
class ControleInscricoesEstaduaisAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'ultimo_documento', 'ultima_conferencia'
    list_display_links = list_display

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not ControleInscricoesEstaduais.objects.exists()


@admin.register(InscricoesEstaduais)
class InscricoesEstaduaisAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'cnpj', 'inscricao_estadual', 'estado', 'habilitado', 'ultima_conferencia',
    list_display_links = list_display
    search_fields = 'cnpj', 'inscricao_estadual',


# @admin.register(VendedoresRegioes)
# class VendedoresRegioesAdmin(BaseModelAdminRedRequired):
#     list_display = 'id', 'vendedor', 'regiao',
#     list_display_links = list_display
#     ordering = 'vendedor',
#     search_fields = 'vendedor',
#     autocomplete_fields = 'vendedor', 'regiao',
