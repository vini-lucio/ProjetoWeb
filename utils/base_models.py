from django.db import models
from django.contrib.auth import get_user_model
from django.contrib import admin

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
