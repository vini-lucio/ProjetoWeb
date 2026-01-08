from django.db import models
from django.db.models import Count, F, Sum, Q
from django.utils.safestring import mark_safe
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
    origem = models.CharField("Origem", max_length=20, choices=origens, blank=True, null=True)  # type:ignore
    motivo = models.ForeignKey(MotivosRnc, verbose_name="Motivo", on_delete=models.PROTECT, related_name="%(class)s",
                               blank=True, null=True)
    follow_up = models.TextField("Follow-Up", blank=True, null=True)
    custo_adicional = models.DecimalField("Custo Adicional R$", default=0.00, max_digits=15,   # type:ignore
                                          decimal_places=2)
    custo_recuperado = models.DecimalField("Custo Recuperado R$", default=0.00, max_digits=15,   # type:ignore
                                           decimal_places=2)
    descricao = models.TextField("Descrição")
    procedente = models.BooleanField("Procedente", default=False)

    def get_nota(self):
        return NOTAS.objects.filter(NF=self.nota_fiscal, CHAVE_JOB__DESCRICAO=self.job.descricao,
                                    NFE_NAC='SIM').first()

    def link_abrir_sacpm(self):
        """Retorna codigo html com a tag de link para a pagina de abertura de SACPM para ser injetado na
        pagina de admin."""
        return mark_safe('<a href="/home_link/formulario-sacpm/" target="_blank">Link SACPM</a>')

    link_abrir_sacpm.short_description = 'Abrir SACPM'

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
        descricao = nota.notas_nfe_log.filter(Q(DESCRICAO__icontains='NF CANCELADA') | Q(  # type:ignore
            DESCRICAO__icontains='NFe REJEITADA'))
        descricao = descricao.order_by('-pk').first()
        if not descricao:
            return ''
        return descricao.DESCRICAO

    descricao_cancelamento.fget.short_description = 'Descrição Cancelamento'  # type:ignore

    def __str__(self) -> str:
        return f'{self.job} - {self.nota_fiscal}'

    @classmethod
    def quantidade_por_responsavel(cls, data_inicio, data_fim):
        """Lista a quantidade de RNCs por responsavel.

        Parametros:
        -----------
        :data_inicio (Date): com a data inicial
        :data_fim (Date): com a data final

        Retorno:
        --------
        :ValuesQuerySet: com as quantidades de RNCs por responsavel"""
        rncs = cls.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        rncs = rncs.values('responsavel__nome').annotate(quantidade=Count('pk'))
        return rncs.order_by('-quantidade')

    @classmethod
    def custo_nao_recuperado_por_responsavel(cls, data_inicio, data_fim):
        """Lista o custo não recuperado de RNCs por responsavel.

        Parametros:
        -----------
        :data_inicio (Date): com a data inicial
        :data_fim (Date): com a data final

        Retorno:
        --------
        :ValuesQuerySet: com os custos não recuperados de RNCs por responsavel"""
        rncs = cls.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        rncs = rncs.values('responsavel__nome').annotate(
            custo_nao_recuperado=Sum(F('custo_adicional') - F('custo_recuperado')))
        return rncs.order_by('-custo_nao_recuperado')

    @classmethod
    def totais(cls, data_inicio, data_fim):
        """Lista os custos totais das RNCs e quantidade total.

        Parametros:
        -----------
        :data_inicio (Date): com a data inicial
        :data_fim (Date): com a data final

        Retorno:
        --------
        :ValuesQuerySet: com os custos e quantidades totais"""
        rncs = cls.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        rncs = rncs.aggregate(
            custo_total=Sum('custo_adicional'),
            custo_recuperado_total=Sum('custo_recuperado'),
            custo_nao_recuperado_total=Sum(F('custo_adicional') - F('custo_recuperado')),
            quantidade_total=Count('pk'),)

        rncs.update({'custo_recuperado_percentual': 100})
        if rncs.get('custo_total'):
            rncs.update({'custo_recuperado_percentual': rncs['custo_recuperado_total'] / rncs['custo_total'] * 100})

        return rncs

    @classmethod
    def quantidade_por_origem(cls, data_inicio, data_fim):
        """Lista a quantidade de RNCs por origem.

        Parametros:
        -----------
        :data_inicio (Date): com a data inicial
        :data_fim (Date): com a data final

        Retorno:
        --------
        :ValuesQuerySet: com as quantidades de RNCs por origem"""
        rncs = cls.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        rncs = rncs.values('origem').annotate(quantidade=Count('pk'))
        return rncs.order_by('-quantidade')

    @classmethod
    def quantidade_por_motivo(cls, data_inicio, data_fim):
        """Lista a quantidade de RNCs por motivo.

        Parametros:
        -----------
        :data_inicio (Date): com a data inicial
        :data_fim (Date): com a data final

        Retorno:
        --------
        :ValuesQuerySet: com as quantidades de RNCs por motivo"""
        rncs = cls.objects.filter(data__gte=data_inicio, data__lte=data_fim)
        rncs = rncs.values('motivo__descricao').annotate(quantidade=Count('pk'))
        return rncs.order_by('-quantidade')
