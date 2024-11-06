from django.db import models
from django.contrib.auth import get_user_model

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
