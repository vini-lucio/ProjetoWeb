from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from home.models import Vendedores
from rh.models import Funcionarios
from utils.choices import meses as meses_choices
from utils.site_setup import get_consultores_tecnicos_ativos


class Indicadores(models.Model):
    class Meta:
        verbose_name = 'Indicador'
        verbose_name_plural = 'Indicadores'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='indicadores_unique_descricao',
                violation_error_message="Descrição é unico em Indicadores"
            ),
        ]

    descricao = models.CharField("Descricao", max_length=50)

    def __str__(self) -> str:
        return self.descricao


class IndicadoresPeriodos(models.Model):
    class Meta:
        verbose_name = "Indicador Periodo"
        verbose_name_plural = "Indicadores Periodos"
        constraints = [
            models.UniqueConstraint(
                fields=['ano_referencia', 'mes_referencia',],
                name='indicadoresperiodos_unique',
                violation_error_message="Indicador, Ano e Mes de referencia são unicos em Indicadores Periodos"
            ),
        ]

    meses = meses_choices

    ano_referencia = models.IntegerField("Ano Referencia")
    mes_referencia = models.IntegerField("Mes Referencia", choices=meses)  # type:ignore
    data_inicio = models.DateField("Data Inicio", auto_now=False, auto_now_add=False)
    data_fim = models.DateField("Data Fim", auto_now=False, auto_now_add=False)
    primeiro_dia_util = models.DateField("Primeiro Dia Util", auto_now=False, auto_now_add=False)
    primeiro_dia_util_proximo_mes = models.DateField("Primeiro Dia Util do Proximo Mês", auto_now=False,
                                                     auto_now_add=False)
    dias_uteis_considerar = models.DecimalField("Dias Uteis Considerar", default=0.00,  # type:ignore
                                                max_digits=5, decimal_places=2)
    dias_uteis_reais = models.DecimalField("Dias Uteis Reais", default=0.00,  # type:ignore
                                           max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f'{self.ano_referencia} / {self.mes_referencia:02d}'

    def save(self, *args, **kwargs):
        novo = True if not self.pk else False
        super().save(*args, **kwargs)

        if novo:
            indicadores = Indicadores.objects.all()
            for indicador in indicadores:
                instancia = IndicadoresValores(indicador=indicador, periodo=self,)
                instancia.full_clean()
                instancia.save()


class IndicadoresValores(models.Model):
    class Meta:
        verbose_name = "Indicador Valor"
        verbose_name_plural = "Indicadores Valores"
        constraints = [
            models.UniqueConstraint(
                fields=['indicador', 'periodo',],
                name='indicadoresvalores_unique',
                violation_error_message="Indicador e periodo são unicos em Indicadores Valores"
            ),
        ]

    indicador = models.ForeignKey(Indicadores, verbose_name="Indicador", on_delete=models.PROTECT,
                                  related_name="%(class)s")
    periodo = models.ForeignKey(IndicadoresPeriodos, verbose_name="Periodo", on_delete=models.PROTECT,
                                related_name="%(class)s")
    valor_meta = models.DecimalField("Valor Meta", default=0.00, max_digits=15, decimal_places=2)  # type:ignore
    valor_real = models.DecimalField("Valor Real", default=0.00, max_digits=15, decimal_places=2)  # type:ignore

    def save(self, *args, **kwargs):
        novo = True if not self.pk else False
        super().save(*args, **kwargs)

        if novo:
            if self.indicador.descricao == 'Meta Carteiras':
                carteiras = get_consultores_tecnicos_ativos()
                for carteira in carteiras:
                    instancia = MetasCarteiras(indicador_valor=self, vendedor=carteira,
                                               responsavel=carteira.responsavel)
                    instancia.full_clean()
                    instancia.save()

    def valor_meta_total(self, classe_somar):
        metas = classe_somar.objects.filter(indicador_valor=self.pk, considerar_total=True)
        metas = metas.aggregate(valor_meta_total=Sum('valor_meta'))

        valor_meta_total = metas.get('valor_meta_total', Decimal(0))

        return valor_meta_total if valor_meta_total else Decimal(0)

    def valor_real_total(self, classe_somar):
        metas = classe_somar.objects.filter(indicador_valor=self.pk, considerar_total=True)
        metas = metas.aggregate(valor_real_total=Sum('valor_real'))

        valor_real_total = metas.get('valor_real_total', Decimal(0))

        return valor_real_total if valor_real_total else Decimal(0)

    def atualizar_valor_meta(self, classe_somar):
        valor_atualizado = self.valor_meta_total(classe_somar)
        self.valor_meta = valor_atualizado
        self.full_clean()
        self.save()

    def atualizar_valor_real(self, classe_somar):
        valor_atualizado = self.valor_real_total(classe_somar)
        self.valor_real = valor_atualizado
        self.full_clean()
        self.save()

    def atualizar_valores(self, classe_somar):
        self.atualizar_valor_meta(classe_somar)
        self.atualizar_valor_real(classe_somar)

    def __str__(self) -> str:
        return f'{self.indicador} - {self.periodo}'


class MetasCarteiras(models.Model):
    class Meta:
        verbose_name = "Meta Carteira"
        verbose_name_plural = "Metas Carteiras"
        constraints = [
            models.UniqueConstraint(
                fields=['indicador_valor', 'vendedor',],
                name='metascarteiras_unique',
                violation_error_message="Indicador e Vendedor são unicos em Metas Carteiras"
            ),
        ]

    indicador_valor = models.ForeignKey(IndicadoresValores, verbose_name="Indicador Valor", on_delete=models.CASCADE,
                                        related_name="%(class)s")
    vendedor = models.ForeignKey(Vendedores, verbose_name="Vendedor", on_delete=models.PROTECT,
                                 related_name="%(class)s")
    responsavel = models.ForeignKey(Funcionarios, verbose_name="Responsavel", on_delete=models.PROTECT,
                                    related_name="%(class)s", null=True, blank=True)
    valor_meta = models.DecimalField("Valor Meta", default=0.00, max_digits=15, decimal_places=2)  # type:ignore
    valor_real = models.DecimalField("Valor Real", default=0.00, max_digits=15, decimal_places=2)  # type:ignore
    considerar_total = models.BooleanField("Considerar Valores no Total", default=False)

    def clean(self):
        super().clean()
        if self.indicador_valor_id and self.indicador_valor.indicador.descricao != 'Meta Carteiras':  # type:ignore
            raise ValidationError({'indicador_valor': 'Indicador precisa ser "Meta Carteiras"'})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self.indicador_valor.atualizar_valores(self.__class__)

    def delete(self, *args, **kwargs):
        super_delete = super().delete(*args, **kwargs)

        self.indicador_valor.atualizar_valores(self.__class__)

        return super_delete

    def __str__(self) -> str:
        return f'{self.indicador_valor} | {self.vendedor}'
