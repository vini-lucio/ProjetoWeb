from django.db import models
from analysis.models import NOTAS
from home.models import Jobs, Responsaveis
from utils.base_models import BaseLogModel
from datetime import date


class MotivosRnc(models.Model):
    class Meta:
        verbose_name = 'Motivo RNC'
        verbose_name_plural = 'Motivos RNC'
        ordering = 'descricao',
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='motivos_rnc_unique_descricao',
                violation_error_message="Descrição é campo unico"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=50)

    def __str__(self) -> str:
        return self.descricao


class RncNotas(BaseLogModel):
    class Meta:
        verbose_name = 'RNC Nota'
        verbose_name_plural = 'RNC Notas'
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'nota_fiscal',],
                name='rnc_notas_unique_nota',
                violation_error_message="Job e Nota Fiscal são campos unicos"
            ),
        ]

    origens = {
        'INTERNO': 'Interno',
        'EXTERNO': 'Externo',
    }

    job = models.ForeignKey(Jobs, verbose_name="Job", on_delete=models.PROTECT, related_name="%(class)s")
    nota_fiscal = models.IntegerField("Nº Nota Fiscal")
    data = models.DateField("Data", auto_now=False, auto_now_add=False, default=date.today)
    responsavel = models.ForeignKey(Responsaveis, verbose_name="Responsavel", on_delete=models.PROTECT,
                                    related_name="%(class)s")
    acao_imediata = models.TextField("Ação Imediata")
    origem = models.CharField("Origem", max_length=20, choices=origens)  # type:ignore
    motivo = models.ForeignKey(MotivosRnc, verbose_name="Motivo", on_delete=models.PROTECT, related_name="%(class)s")
    follow_up = models.TextField("Follow-Up", blank=True, null=True)
    custo_adicional = models.DecimalField("Custo Adicional R$", default=0.00, max_digits=15,   # type:ignore
                                          decimal_places=2)
    custo_recuperado = models.DecimalField("Custo Recuperado R$", default=0.00, max_digits=15,   # type:ignore
                                           decimal_places=2)
    descricao = models.TextField("Descrição")

    def get_nota(self):
        return NOTAS.objects.filter(NF=self.nota_fiscal, CHAVE_JOB__DESCRICAO=self.job.descricao,
                                    NFE_NAC='SIM').first()

    @property
    def cliente(self):
        nota = self.get_nota()
        if not nota:
            return ''
        return nota.CHAVE_CLIENTE.NOMERED  # type:ignore

    cliente.fget.short_description = 'Cliente'  # type:ignore

    @property
    def descricao_cancelamento(self):
        nota = self.get_nota()
        if not nota:
            return ''
        descricao = nota.notas_nfe_log.filter(DESCRICAO__icontains='NF CANCELADA')  # type:ignore
        descricao = descricao.order_by('-pk').first()
        if not descricao:
            return ''
        return descricao.DESCRICAO

    descricao_cancelamento.fget.short_description = 'Descrição Cancelamento'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nota_fiscal}'
