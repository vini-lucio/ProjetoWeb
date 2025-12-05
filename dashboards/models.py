from typing import Self
from dashboards.services import get_relatorios_vendas
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from home.models import Vendedores
from rh.models import Funcionarios
from utils.choices import meses as meses_choices
from utils.site_setup import get_consultores_tecnicos_ativos, get_site_setup


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
        """Ao incluir um novo Indicador Periodo, são adicionados em Indicadores Valores todos os Indicadores com
        o novo Indicador Periodo"""
        novo = True if not self.pk else False
        super().save(*args, **kwargs)

        if novo:
            indicadores = Indicadores.objects.all()
            for indicador in indicadores:
                instancia = IndicadoresValores(indicador=indicador, periodo=self,)
                instancia.full_clean()
                instancia.save()

    @classmethod
    def get_indicador_periodo_create(cls) -> Self | None:
        """Busca Indicador Periodo do periodo definido em Site Setup. Se não houver ele é criado com o definido em
        Site Setup.

        Retorno:
        --------
        :IndicadoresPeriodo: do periodo em Site Setup
        :None: caso não exista Site Setup"""
        site_setup = get_site_setup()
        if site_setup:
            primeiro_dia_mes = site_setup.primeiro_dia_mes
            ano = primeiro_dia_mes.year
            mes = primeiro_dia_mes.month

            periodo = cls.objects.filter(ano_referencia=ano, mes_referencia=mes).first()
            if periodo:
                return periodo

            instancia = cls(
                ano_referencia=ano,
                mes_referencia=mes,
                data_inicio=site_setup.primeiro_dia_mes,
                data_fim=site_setup.ultimo_dia_mes,
                primeiro_dia_util=site_setup.primeiro_dia_util_mes,
                primeiro_dia_util_proximo_mes=site_setup.primeiro_dia_util_proximo_mes,
                dias_uteis_considerar=site_setup.dias_uteis_mes,
                dias_uteis_reais=site_setup.dias_uteis_mes_reais
            )
            instancia.full_clean()
            instancia.save()
            return instancia


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

    @property
    def indicador_descricao(self):
        return self.indicador.descricao

    @property
    def periodo_descricao(self):
        return str(self.periodo)

    def save(self, *args, **kwargs):
        """Ao incluir um novo Indicador Valor, são adicionados em Metas Carteiras todos os Vendedores ativos com
        o novo Indicador Valor"""
        novo = True if not self.pk else False
        super().save(*args, **kwargs)

        if novo:
            if self.indicador.descricao == 'Meta Carteiras':
                carteiras = get_consultores_tecnicos_ativos()
                for carteira in carteiras:
                    instancia = MetasCarteiras(indicador_valor=self, vendedor=carteira,
                                               responsavel=carteira.responsavel, valor_meta=carteira.meta_mes,
                                               considerar_total=carteira.considerar_total)
                    instancia.full_clean()
                    instancia.save()

    def valor_meta_total(self, classe_somar) -> Decimal:
        """Retorna soma de valores de metas de classe filho (que estão marcadas para considerar no total).

        Parametros:
        -----------
        :classe_somar (class): classe filho com valor meta

        Retorno:
        --------
        :Decimal: valor total da soma de meta"""
        metas = classe_somar.objects.filter(indicador_valor=self.pk, considerar_total=True)
        metas = metas.aggregate(valor_meta_total=Sum('valor_meta'))

        valor_meta_total = metas.get('valor_meta_total', Decimal(0))

        return valor_meta_total if valor_meta_total else Decimal(0)

    def valor_real_total(self, classe_somar) -> Decimal:
        """Retorna soma de valores reais de metas de classe filho (que estão marcadas para considerar no total).

        Parametros:
        -----------
        :classe_somar (class): classe filho com valor real da meta

        Retorno:
        --------
        :Decimal: valor total da soma real da meta"""
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

    @property
    def indicador_valor_descricao(self):
        return str(self.indicador_valor)

    @property
    def vendedor_nome(self):
        return str(self.vendedor)

    @property
    def responsavel_nome(self):
        if not self.responsavel:
            return ''
        return self.responsavel.nome

    def clean(self):
        """Garante que indicador seja 'Meta Carteiras'"""
        super().clean()
        if self.indicador_valor_id and self.indicador_valor.indicador.descricao != 'Meta Carteiras':  # type:ignore
            raise ValidationError({'indicador_valor': 'Indicador precisa ser "Meta Carteiras"'})

    def save(self, *args, **kwargs):
        """Ao salvar, atualiza automaticamente valores reais e de meta em Indicador Valores"""
        super().save(*args, **kwargs)

        self.indicador_valor.atualizar_valores(self.__class__)

    def delete(self, *args, **kwargs):
        """Ao excluir, atualiza automaticamente valores reais e de meta em Indicador Valores"""
        super_delete = super().delete(*args, **kwargs)

        self.indicador_valor.atualizar_valores(self.__class__)

        return super_delete

    def __str__(self) -> str:
        return f'{self.indicador_valor} | {self.vendedor}'

    @classmethod
    def atualizar_metas_carteiras_valores(cls, carteira: Vendedores | None = None):
        """Atualiza valores de meta por carteira definido em Vendedores e atualiza valores de vendas reais no periodo
        definido em Site Setup de todas as carteiras ou na carteira especifica.

        Parametros:
        -----------
        :carteira (Vendedor, opcional): com carteira especifica ou se não for definido será atualizado todas as carteiras"""
        indicador_periodo = IndicadoresPeriodos.get_indicador_periodo_create()
        inicio = indicador_periodo.data_inicio if indicador_periodo else None
        fim = indicador_periodo.data_fim if indicador_periodo else None

        indicador_valor = IndicadoresValores.objects.filter(indicador__descricao='Meta Carteiras',
                                                            periodo=indicador_periodo).first()

        metas_carteiras = cls.objects.filter(indicador_valor=indicador_valor)
        if carteira:
            metas_carteiras = metas_carteiras.filter(vendedor=carteira)

        for meta_carteira in metas_carteiras:
            vendedor = meta_carteira.vendedor
            carteira_parametros = vendedor.carteira_parametros()
            valor = get_relatorios_vendas('faturamentos', inicio=inicio, fim=fim, **carteira_parametros)
            valor = valor[0]['VALOR_MERCADORIAS'] if valor else 0

            meta_carteira.responsavel = vendedor.responsavel
            meta_carteira.valor_meta = str(round(vendedor.meta_mes, 2))
            meta_carteira.valor_real = str(round(valor, 2))
            meta_carteira.considerar_total = vendedor.considerar_total
            meta_carteira.full_clean()
            meta_carteira.save()
