from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from home.models import (HomeLinks, SiteSetup, HomeLinksDocumentos, AssistentesTecnicos, AssistentesTecnicosAgenda,
                         Jobs, Paises, Estados, Cidades, Bancos, Atualizacoes, ProdutosModelos, ProdutosModelosTopicos,
                         ProdutosModelosTags, Unidades, Produtos)
from django_summernote.admin import SummernoteModelAdmin
from utils.base_models import (BaseModelAdminRedRequired, BaseModelAdminRedRequiredLog, AdminRedRequiredMixIn,
                               AdminLogMixIn)
from utils.exportar_excel import arquivo_excel
import home.services as services
import os
import zipfile
import tempfile


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
                'meta_mes', 'dias_uteis_mes', 'meta_diaria',
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
    list_display = 'id', 'descricao', 'status',
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


@admin.register(Estados)
class EstadosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'uf', 'sigla',
    list_display_links = list_display
    ordering = 'uf',
    search_fields = 'uf', 'sigla',
    readonly_fields = 'chave_migracao',


@admin.register(Cidades)
class CidadesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome', 'estado',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',
    readonly_fields = 'chave_migracao',


@admin.register(Bancos)
class BancosAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'nome',
    list_display_links = list_display
    ordering = 'nome',
    search_fields = 'nome',


@admin.register(Atualizacoes)
class AtualizacoesAdmin(BaseModelAdminRedRequired):
    list_display = 'id', 'descricao',
    list_display_links = list_display
    ordering = 'descricao',
    search_fields = 'descricao',
    actions = 'exportar_atualizacoes',

    campos_exportar = ['descricao', 'nome_funcao']

    @admin.action(description="Exportar .XLSX Selecionados .ZIP")
    def exportar_atualizacoes(self, request, queryset):
        campos_exportar = [field for field in self.campos_exportar]

        with tempfile.TemporaryDirectory() as pasta_temporaria:
            caminhos_arquivos_compactar = []

            for obj in queryset:
                nome_arquivo = getattr(obj, campos_exportar[1])
                funcao = getattr(services, getattr(obj, campos_exportar[1]))
                resultado = funcao()

                cabecalho = [cabecalho for cabecalho in resultado[0].keys()]

                conteudo = []
                for registro in resultado:
                    linha = [valor for chave, valor in registro.items()]
                    conteudo.append(linha)

                workbook = arquivo_excel(conteudo, cabecalho)

                caminho_arquivo_excel = os.path.join(pasta_temporaria, f'{nome_arquivo}.xlsx')
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
