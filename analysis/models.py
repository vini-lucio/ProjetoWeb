from django.db import models
from utils.base_models import ReadOnlyMixin


class CANAIS_VENDA(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."CANAIS_VENDA"'
        verbose_name = 'Canal de Vendas'
        verbose_name_plural = 'Canais de Vendas'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=30, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class VENDEDORES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."VENDEDORES"'
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'

    CODVENDEDOR = models.IntegerField("ID", primary_key=True)
    NOMERED = models.CharField("Nome Reduzido", max_length=13, null=True, blank=True)
    INATIVO = models.CharField("Inativo", max_length=3, null=True, blank=True)
    CHAVE_CANAL = models.ForeignKey(CANAIS_VENDA, db_column="CHAVE_CANAL", verbose_name="Canal de Vendas",
                                    on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    def __str__(self):
        return self.NOMERED


class REGIOES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."REGIOES"'
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'

    CHAVE = models.IntegerField("ID", primary_key=True)
    REGIAO = models.CharField("Região", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.REGIAO


class ESTADOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."ESTADOS"'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    CHAVE = models.IntegerField("ID", primary_key=True)
    ESTADO = models.CharField("Nome Reduzido", max_length=20, null=True, blank=True)
    SIGLA = models.CharField("Inativo", max_length=2, null=True, blank=True, unique=True)
    CHAVE_REGIAO = models.ForeignKey(REGIOES, db_column="CHAVE_REGIAO", verbose_name="Região",
                                     on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    def __str__(self):
        return self.ESTADO


class MATRIZ_ICMS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."MATRIZ_ICMS"'
        verbose_name = 'Estado ICMS'
        verbose_name_plural = 'Estados ICMS'

    CHAVE = models.IntegerField("ID", primary_key=True)
    UF_EMITENTE = models.ForeignKey(ESTADOS, db_column="UF_EMITENTE", verbose_name="UF Emitente",
                                    on_delete=models.PROTECT, related_name="%(class)s_uf_emitente", null=True,
                                    blank=True)
    UF_DESTINO = models.ForeignKey(ESTADOS, db_column="UF_DESTINO", verbose_name="UF Destino", on_delete=models.PROTECT,
                                   related_name="%(class)s_uf_destino", null=True, blank=True)
    ALIQUOTA = models.DecimalField("Aliquota %", max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f'{self.UF_EMITENTE.SIGLA}-{self.UF_DESTINO.SIGLA}'  # type:ignore


class FAIXAS_CEP(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."FAIXAS_CEP"'
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'

    CHAVE = models.IntegerField("ID", primary_key=True)
    UF = models.ForeignKey(ESTADOS, db_column="UF", verbose_name="UF", on_delete=models.PROTECT, to_field="SIGLA",
                           related_name="%(class)s", null=True, blank=True)
    CIDADE = models.CharField("Inativo", max_length=50, null=True, blank=True)

    def __str__(self):
        return self.CIDADE


class UNIDADES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."UNIDADES"'
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'

    CHAVE = models.IntegerField("ID", primary_key=True)
    UNIDADE = models.CharField("Nome Reduzido", max_length=6, null=True, blank=True)
    DESCRICAO = models.CharField("Inativo", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class FAMILIA_PRODUTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."FAMILIA_PRODUTOS"'
        verbose_name = 'Familia Produtos'
        verbose_name_plural = 'Familias Produtos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    FAMILIA = models.CharField("Familia", max_length=50, null=True, blank=True)

    def __str__(self):
        return self.FAMILIA


class PRODUTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."PRODUTOS"'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    CPROD = models.IntegerField("ID", primary_key=True)
    CODIGO = models.CharField("Codigo", max_length=60, null=True, blank=True)
    CHAVE_FAMILIA = models.ForeignKey(FAMILIA_PRODUTOS, db_column="CHAVE_FAMILIA", verbose_name="Familia",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_UNIDADE = models.ForeignKey(UNIDADES, db_column="CHAVE_UNIDADE", verbose_name="Unidade",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    DESCRICAO = models.CharField("Descrição", max_length=120, null=True, blank=True)
    PESO_LIQUIDO = models.DecimalField("Peso Liquido", max_digits=8, decimal_places=4, null=True, blank=True)
    PESO_BRUTO = models.DecimalField("Peso Bruto", max_digits=8, decimal_places=4, null=True, blank=True)
    FORA_DE_LINHA = models.CharField("Fora de Linha", max_length=3, null=True, blank=True)
    CODIGO_BARRA = models.CharField("Codigo de Barras (EAN13)", max_length=13, null=True, blank=True)
    CARACTERISTICA2 = models.CharField("Caracteristica 2", max_length=4000, null=True, blank=True)

    def __str__(self):
        return self.CODIGO
