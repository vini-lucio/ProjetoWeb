from django.db import models
from utils.base_models import ReadOnlyMixin


class VENDEDORES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."VENDEDORES"'
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'

    CODVENDEDOR = models.IntegerField("ID", primary_key=True)
    NOMERED = models.CharField("Nome Reduzido", max_length=13, null=True, blank=True)
    INATIVO = models.CharField("Inativo", max_length=3, null=True, blank=True)

    def __str__(self):
        return self.NOMERED
