from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.http import HttpRequest, HttpResponse
import csv
import openpyxl

User = get_user_model()


class BaseLogModel(models.Model):
    class Meta:
        abstract = True

    criado_por = models.ForeignKey(User, verbose_name="Criado Por", on_delete=models.PROTECT,
                                   related_name="%(class)s_criado_por", null=True, blank=True)
    criado_em = models.DateTimeField("Criado Em", auto_now_add=True, auto_now=False)
    atualizado_por = models.ForeignKey(User, verbose_name="Atualizado Por", on_delete=models.PROTECT,
                                       related_name="%(class)s_atualizado_por", null=True, blank=True)
    atualizado_em = models.DateTimeField("Atualizado Em", auto_now_add=False, auto_now=True)


class BaseModelAdminRedRequired(admin.ModelAdmin):
    class Meta:
        abstract = True

    class Media:
        css = {'all': ('admin/css/style.css',)}


class BaseModelAdminRedRequiredLog(BaseModelAdminRedRequired):
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


class BaseViewAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        # return super().has_add_permission(request)
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        # return super().has_change_permission(request, obj)
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        # return super().has_delete_permission(request, obj)
        return False


class ExportarCsvMixIn:
    # TODO: ajustar exportação dos formatos corretamente
    def exportar_csv(self, request, queryset):
        meta = self.model._meta  # type:ignore
        campos = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)

        writer = csv.writer(response)

        writer.writerow(campos)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in campos])

        return response

    exportar_csv.short_description = "Exportar .CSV Selecionados"


class ExportarXlsxMixIn:
    campos_exportar = []

    def exportar_excel(self, request, queryset):
        meta = self.model._meta  # type:ignore

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(meta)

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        if worksheet:
            # worksheet.title = "Book Author View"

            # colunas = [field.name for field in meta.fields]
            if self.campos_exportar:  # type:ignore
                colunas = [field for field in self.campos_exportar]  # type:ignore
            else:
                colunas = [field for field in self.list_display]  # type:ignore
            worksheet.append(colunas)

            for obj in queryset:
                worksheet.append([getattr(obj, field) for field in colunas])

            workbook.save(response)  # type:ignore
        return response

    exportar_excel.short_description = "Exportar .XLSX Selecionados"
