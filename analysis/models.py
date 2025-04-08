from django.db import models
from django.db.models import F, Count
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


class CLIENTES_TIPOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."CLIENTES_TIPOS"'
        verbose_name = 'Tipo de Clientes'
        verbose_name_plural = 'Tipos de Clientes'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class STATUS_ORCAMENTOS_ITENS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."STATUS_ORCAMENTOS_ITENS"'
        verbose_name = 'Status Orçamentos Produtos'
        verbose_name_plural = 'Status Orçamentos Produtos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=50, null=True, blank=True)
    TIPO = models.CharField("Tipo", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class GRUPO_ECONOMICO(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."GRUPO_ECONOMICO"'
        verbose_name = 'Grupo Economico'
        verbose_name_plural = 'Grupos Economicos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=50, null=True, blank=True)

    @property
    def clientes_ativos(self):
        ativos = self.clientes.all()  # type:ignore
        ativos = ativos.exclude(STATUS='X')
        return ativos

    @property
    def quantidade_clientes_ativos(self):
        clientes_ativos = self.clientes_ativos.count()
        return clientes_ativos

    @property
    def quantidade_clientes_ativos_por_tipo(self):
        clientes_ativos = self.clientes_ativos
        quantidade_tipos = clientes_ativos.values(TIPO=F('CHAVE_TIPO__DESCRICAO')).annotate(
            QUANTIDADE=Count('CHAVE_TIPO')).order_by('-QUANTIDADE')
        return quantidade_tipos

    @property
    def quantidade_clientes_ativos_por_carteira(self):
        clientes_ativos = self.clientes_ativos
        quantidade_carteiras = clientes_ativos.values(CARTEIRA=F('CHAVE_VENDEDOR3__NOMERED')).annotate(
            QUANTIDADE=Count('CHAVE_VENDEDOR3')).order_by('-QUANTIDADE')
        return quantidade_carteiras

    @property
    def quantidade_eventos_em_aberto(self):
        clientes = self.clientes.all()  # type:ignore
        quantidade = 0
        if clientes:
            quantidade = CLIENTES_HISTORICO.objects.using('analysis').filter(DATA_REALIZADO__isnull=True,
                                                                             CHAVE_CLIENTE__in=clientes).count()
        return quantidade

    def __str__(self):
        return self.DESCRICAO


class CLIENTES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."CLIENTES"'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    CODCLI = models.IntegerField("ID", primary_key=True)
    NOMERED = models.CharField("Nome Reduzido", max_length=20, null=True, blank=True)
    CODVEND = models.ForeignKey(VENDEDORES, db_column="CODVEND", verbose_name="1º Representante",
                                on_delete=models.PROTECT, related_name="%(class)s_codvend", null=True, blank=True)
    CHAVE_VENDEDOR2 = models.ForeignKey(VENDEDORES, db_column="CHAVE_VENDEDOR2", verbose_name="2º Representante",
                                        on_delete=models.PROTECT, related_name="%(class)s_chave_vendedor2", null=True,
                                        blank=True)
    CHAVE_VENDEDOR3 = models.ForeignKey(VENDEDORES, db_column="CHAVE_VENDEDOR3", verbose_name="Consultor Tecnico",
                                        on_delete=models.PROTECT, related_name="%(class)s_chave_vendedor3", null=True,
                                        blank=True)
    STATUS = models.CharField("Status", max_length=1, null=True, blank=True)
    UF = models.ForeignKey(ESTADOS, db_column="UF", verbose_name="Estado Principal", on_delete=models.PROTECT,
                           related_name="%(class)s_uf", null=True, blank=True)
    CGC = models.CharField("CNPJ / CPF", max_length=18, null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(CLIENTES_TIPOS, db_column="CHAVE_TIPO", verbose_name="Tipo de Cliente",
                                   on_delete=models.PROTECT, related_name="%(class)s_uf", null=True, blank=True)
    CHAVE_GRUPOECONOMICO = models.ForeignKey(GRUPO_ECONOMICO, db_column="CHAVE_GRUPOECONOMICO",
                                             verbose_name="Grupo Economico", on_delete=models.PROTECT,
                                             related_name="%(class)s", null=True, blank=True)

    def __str__(self):
        return self.NOMERED


class TIPOS_HISTORICO(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."TIPOS_HISTORICO"'
        verbose_name = 'Tipo de Evento'
        verbose_name_plural = 'Tipos de Evento'

    CHAVE = models.IntegerField("ID", primary_key=True)
    TIPO = models.CharField("Tipo", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.TIPO


class V_COLABORADORES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."V_COLABORADORES"'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    CHAVE = models.IntegerField("ID", primary_key=True)
    USUARIO = models.CharField("Usuario", max_length=30, null=True, blank=True)

    def __str__(self):
        return self.USUARIO


class CLIENTES_HISTORICO(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."CLIENTES_HISTORICO"'
        verbose_name = 'Evento Cliente'
        verbose_name_plural = 'Eventos Cliente'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_CLIENTE = models.ForeignKey(CLIENTES, db_column="CHAVE_CLIENTE", verbose_name="Cliente",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    DATA = models.DateField("Data Previsão", auto_now=False, auto_now_add=False, null=True, blank=True)
    DATA_REALIZADO = models.DateField("Data Realizado", auto_now=False, auto_now_add=False, null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(TIPOS_HISTORICO, db_column="CHAVE_TIPO", verbose_name="Tipo",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    ASSUNTO = models.CharField("Assunto", max_length=40, null=True, blank=True)
    CHAVE_RESPONSAVEL = models.ForeignKey(V_COLABORADORES, db_column="CHAVE_RESPONSAVEL", verbose_name="Responsavel",
                                          on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    OBSERVACOES_EVENTO = models.TextField("Observações Evento", null=True, blank=True)
    OBSERVACOES_EVENTO_FECHAMENTO = models.TextField("Observações Evento Fechamento", null=True, blank=True)

    def __str__(self):
        return self.CHAVE


class PEDIDOS_TIPOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."PEDIDOS_TIPOS"'
        verbose_name = 'Tipo de Pedido'
        verbose_name_plural = 'Tipos de Pedido'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=50, null=True, blank=True)
    VALOR_COMERCIAL = models.CharField("Valor Comercial", max_length=3, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class ORCAMENTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."ORCAMENTOS"'
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    NUMPED = models.IntegerField("Nº Orçamento")
    DATA_PEDIDO = models.DateField("Data Orçamento", auto_now=False, auto_now_add=False, null=True, blank=True)
    CHAVE_CLIENTE = models.ForeignKey(CLIENTES, db_column="CHAVE_CLIENTE", verbose_name="Cliente",
                                      on_delete=models.PROTECT, related_name="%(class)s_chave_cliente", null=True,
                                      blank=True)
    VALOR_TOTAL = models.DecimalField("Valor Total", max_digits=22, decimal_places=6, null=True, blank=True)
    STATUS = models.CharField("Status", max_length=15, null=True, blank=True)
    VALOR_FRETE = models.DecimalField("Valor Frete", max_digits=22, decimal_places=6, null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(PEDIDOS_TIPOS, db_column="CHAVE_TIPO", verbose_name="Tipo de Orçamento",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    REGISTRO_OPORTUNIDADE = models.CharField("Oportunidade", max_length=3, null=True, blank=True)
    VALOR_FRETE_EMPRESA = models.DecimalField("Valor Frete Empresa", max_digits=22, decimal_places=6, null=True,
                                              blank=True)
    FRETE_INCL_ITEM = models.CharField("Frete Incluso nos Itens", max_length=3, null=True, blank=True)
    VALOR_FRETE_INCL_ITEM = models.DecimalField("Valor Frete Incluso nos Itens", max_digits=22, decimal_places=6,
                                                null=True, blank=True)

    def __str__(self):
        return self.NUMPED


class ORCAMENTOS_ITENS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."ORCAMENTOS_ITENS"'
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_PEDIDO = models.ForeignKey(ORCAMENTOS, db_column="CHAVE_PEDIDO", verbose_name="Orçamento",
                                     on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_PRODUTO = models.ForeignKey(PRODUTOS, db_column="CHAVE_PRODUTO", verbose_name="Produto",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    QUANTIDADE = models.DecimalField("Quantidade", max_digits=22, decimal_places=6, null=True, blank=True)
    DATA_ENTREGA = models.DateField("Data de Entrega", auto_now=False, auto_now_add=False, null=True, blank=True)
    PRECO_TABELA = models.DecimalField("Preço de Tabela", max_digits=22, decimal_places=6, null=True, blank=True)
    PRECO_VENDA = models.DecimalField("Preço de Venda", max_digits=22, decimal_places=6, null=True, blank=True)
    VALOR_TOTAL = models.DecimalField("Valor Total", max_digits=22, decimal_places=6, null=True, blank=True)
    STATUS = models.CharField("Status", max_length=50, null=True, blank=True)
    RATEIO_FRETE = models.DecimalField("Rateio Frete", max_digits=22, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f'{self.CHAVE_PEDIDO} - {self.CHAVE_PRODUTO}'


class PEDIDOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."PEDIDOS"'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    NUMPED = models.IntegerField("Nº Pedido")
    DATA_PEDIDO = models.DateField("Data Pedido", auto_now=False, auto_now_add=False, null=True, blank=True)
    CHAVE_CLIENTE = models.ForeignKey(CLIENTES, db_column="CHAVE_CLIENTE", verbose_name="Cliente",
                                      on_delete=models.PROTECT, related_name="%(class)s_chave_cliente", null=True,
                                      blank=True)
    VALOR_TOTAL = models.DecimalField("Valor Total", max_digits=22, decimal_places=6, null=True, blank=True)
    STATUS = models.CharField("Status", max_length=15, null=True, blank=True)
    VALOR_FRETE = models.DecimalField("Valor Frete", max_digits=22, decimal_places=6, null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(PEDIDOS_TIPOS, db_column="CHAVE_TIPO", verbose_name="Tipo de Orçamento",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    VALOR_FRETE_EMPRESA = models.DecimalField("Valor Frete Empresa", max_digits=22, decimal_places=6, null=True,
                                              blank=True)
    FRETE_INCL_ITEM = models.CharField("Frete Incluso nos Itens", max_length=3, null=True, blank=True)
    VALOR_FRETE_INCL_ITEM = models.DecimalField("Valor Frete Incluso nos Itens", max_digits=22, decimal_places=6,
                                                null=True, blank=True)

    def __str__(self):
        return self.NUMPED
