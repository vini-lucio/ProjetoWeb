from django.db import models
from utils.converter import converter_data_django_para_str_ddmmyyyy


class Admissoes(models.Model):
    class Meta:
        managed = False
        db_table = 'rh_admissao_view'
        verbose_name = 'Relatorio Admissão'
        verbose_name_plural = 'Relatorio Admissões'

    id = models.IntegerField(primary_key=True)
    job = models.CharField("Job", max_length=30, null=True, blank=True)
    registro = models.IntegerField("Registro", null=True, blank=True)
    nome = models.CharField("Nome", max_length=100, null=True, blank=True)
    mes_entrada = models.DecimalField("Mes Entrada", max_digits=2, decimal_places=0, null=True, blank=True)
    data_entrada = models.DateField("Data Entrada", auto_now=False, auto_now_add=False, null=True, blank=True)
    tempo_casa_anos = models.DecimalField("Tempo Casa Anos", max_digits=5, decimal_places=1, null=True, blank=True)

    @property
    def data_entrada_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data_entrada)

    data_entrada_as_ddmmyyyy.fget.short_description = 'Data Entrada'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nome} - {self.data_entrada} - {self.tempo_casa_anos} anos'
