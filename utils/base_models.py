from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from utils.exportar_excel import arquivo_excel
from django.core.exceptions import PermissionDenied

User = get_user_model()


class ChaveAnalysisPropertyMixIn:
    @property
    def chave_analysis(self):
        return self.pk  # type:ignore


class ReadOnlyMixin:
    def save(self, *args, **kwargs):
        raise PermissionDenied("Ação não permitida")

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Ação não permitida")


class BaseLogModel(models.Model):
    """Model que adiciona campos de log."""
    class Meta:
        abstract = True

    criado_por = models.ForeignKey(User, verbose_name="Criado Por", on_delete=models.PROTECT,
                                   related_name="%(class)s_criado_por", null=True, blank=True)
    criado_em = models.DateTimeField("Criado Em", auto_now_add=True, auto_now=False)
    atualizado_por = models.ForeignKey(User, verbose_name="Atualizado Por", on_delete=models.PROTECT,
                                       related_name="%(class)s_atualizado_por", null=True, blank=True)
    atualizado_em = models.DateTimeField("Atualizado Em", auto_now_add=False, auto_now=True)


class BaseModelAdminRedRequired(admin.ModelAdmin):
    """Admin Model que perssonaliza estilo css do formulario em admin."""
    class Meta:
        abstract = True

    class Media:
        css = {'all': ('admin/css/style.css',)}


class AdminRedRequiredMixIn:
    """Mix In para Admin Model que perssonaliza estilo css do formulario em admin."""
    class Media:
        css = {'all': ('admin/css/style.css',)}


class BaseModelAdminRedRequiredLog(BaseModelAdminRedRequired):
    """Admin Model que perssonaliza estilo css do formulario e salva logs em admin."""
    class Meta:
        abstract = True

    def save_model(self, request, obj, form, change) -> None:
        if not obj.pk:
            obj.criado_por = request.user
            obj.atualizado_por = request.user
        if change:
            obj.atualizado_por = request.user
        obj.save()
        return super().save_model(request, obj, form, change)


class AdminLogMixIn:
    """Mix In para Admin Model que salva dados de log do formulario em admin."""

    def save_model(self, request, obj, form, change) -> None:
        if not obj.pk:
            obj.criado_por = request.user
            obj.atualizado_por = request.user
        if change:
            obj.atualizado_por = request.user
        obj.save()
        return super().save_model(request, obj, form, change)  # type:ignore


class BaseViewAdmin(admin.ModelAdmin):
    """Admin model para views. Somente leitura do model."""
    class Meta:
        abstract = True

    def has_add_permission(self, request: HttpRequest) -> bool:
        # return super().has_add_permission(request)
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        # return super().has_change_permission(request, obj)
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        # return super().has_delete_permission(request, obj)
        return False


class ExportarXlsxMixIn:
    """Mix In que adiciona ação exportar_excel em admin de exportar para excel a seleção com os campos informados.
    Se não for informado campos_exportar, será considerado para exportação o definido em list_display do admin model.

    Atributos:
    ----------
    :campos_exportar [list]: com o nome dos campos a serem exportados para excel. Não usar chave estrangeira, criar uma property."""
    campos_exportar = []

    def exportar_excel(self, request, queryset):
        meta = self.model._meta  # type:ignore

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(meta)

        if self.campos_exportar:  # type:ignore
            cabecalho = [field for field in self.campos_exportar]  # type:ignore
        else:
            cabecalho = [field for field in self.list_display]  # type:ignore

        conteudo = []
        for obj in queryset:
            linha = [getattr(obj, field) for field in cabecalho]
            conteudo.append(linha)

        workbook = arquivo_excel(conteudo, cabecalho)
        workbook.save(response)  # type:ignore

        return response

    exportar_excel.short_description = "Exportar .XLSX Selecionados"
