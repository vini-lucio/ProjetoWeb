from django.db import models
from django.db.models import Q
from home.models import Jobs
from utils.base_models import BaseLogModel
from utils.converter import converter_data_django_para_str_ddmmyyyy


class Cbo(models.Model):
    class Meta:
        verbose_name = 'CBO'
        verbose_name_plural = 'CBO'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='cbo_unique_descricao',
                violation_error_message="Descrição é unico em CBO"
            ),
        ]

    numero = models.CharField("Numero", max_length=10)
    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.numero} - {self.descricao}'


class Dissidios(BaseLogModel):
    class Meta:
        verbose_name = 'Dissidio'
        verbose_name_plural = 'Dissidios'
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'data',],
                name='dissidios_unique_job_data',
                violation_error_message="Job e Data são unicos em Dissidios"
            ),
            models.CheckConstraint(
                check=Q(dissidio_real__gte=0),
                name='dissidios_check_dissidio_real',
                violation_error_message="Dissidio Real precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(dissidio_adicional__gte=0),
                name='dissidios_check_dissidio_adicional',
                violation_error_message="Dissidio Adicional precisa ser maior ou igual a 0"
            ),
        ]

    job = models.ForeignKey(Jobs, verbose_name="Job", on_delete=models.PROTECT)
    data = models.DateField("Data", auto_now=False, auto_now_add=False)
    dissidio_real = models.DecimalField("Dissidio Real %", max_digits=5, decimal_places=2, default=0.00)  # type:ignore
    dissidio_adicional = models.DecimalField("Dissidio Adicional %", max_digits=5, decimal_places=2,
                                             default=0.00)  # type:ignore
    observacoes = models.CharField("Observações", max_length=300, null=True, blank=True)
    aplicado = models.BooleanField("Dissidio Aplicado?", default=False)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    @property
    def data_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data)

    data_as_ddmmyyyy.fget.short_description = 'Data'  # type:ignore

    @property
    def dissidio_total(self):
        return self.dissidio_real + self.dissidio_adicional

    dissidio_total.fget.short_description = 'Dissidio Total %'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.data_as_ddmmyyyy}'


class Escolaridades(models.Model):
    class Meta:
        verbose_name = 'Escolaridade'
        verbose_name_plural = 'Escolaridades'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='escolaridades_unique_descricao',
                violation_error_message="Descrição é unico em Escolaridades"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao


class TransporteLinhas(models.Model):
    class Meta:
        verbose_name = 'Transporte Linha'
        verbose_name_plural = 'Transporte Linhas'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='transportelinhas_unique_descricao',
                violation_error_message="Descrição é unico em Transporte Linhas"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=50)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.descricao
