from django.apps import apps
from django.db import models
from django.db.models import F, Count, Max, Avg
from django.db.models.expressions import RawSQL
from utils.base_models import ReadOnlyMixin, ChaveAnalysisPropertyMixIn
from utils.converter import somente_digitos, converter_data_django_para_str_ddmmyyyy
from utils.data_hora_atual import hoje, data_inicio_analysis


class JOBS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."JOBS"'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    CODIGO = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=50, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


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


class VENDEDORES(ReadOnlyMixin, ChaveAnalysisPropertyMixIn, models.Model):
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


class ESTADOS(ReadOnlyMixin, ChaveAnalysisPropertyMixIn, models.Model):
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


class LINHA_PRODUTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."LINHA_PRODUTOS"'
        verbose_name = 'Linha Produtos'
        verbose_name_plural = 'Linhas Produtos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    LINHA = models.CharField("Linha", max_length=50, null=True, blank=True)
    CHAVE_FAMILIA = models.ForeignKey(FAMILIA_PRODUTOS, db_column="CHAVE_FAMILIA", verbose_name="Familia",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    def __str__(self):
        return self.LINHA


class GRUPO_PRODUTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."GRUPO_PRODUTOS"'
        verbose_name = 'Grupo Produtos'
        verbose_name_plural = 'Grupos Produtos'

    CHAVE = models.IntegerField("ID", primary_key=True)
    GRUPO = models.CharField("Grupo", max_length=50, null=True, blank=True)
    CHAVE_LINHA = models.ForeignKey(LINHA_PRODUTOS, db_column="CHAVE_LINHA", verbose_name="Linha",
                                    on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    def __str__(self):
        return self.GRUPO


class MARCAS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."MARCAS"'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    CHAVE = models.IntegerField("ID", primary_key=True)
    MARCA = models.CharField("Marca", max_length=50, null=True, blank=True)

    def __str__(self):
        return self.MARCA


class TIPO_PRODUTOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."TIPO_PRODUTOS"'
        verbose_name = 'Tipo de Produto'
        verbose_name_plural = 'Tipos de Produto'

    CHAVE = models.IntegerField("ID", primary_key=True)
    TIPO = models.CharField("Tipo", max_length=20, null=True, blank=True)

    def __str__(self):
        return self.TIPO


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
    CHAVE_LINHA = models.ForeignKey(LINHA_PRODUTOS, db_column="CHAVE_LINHA", verbose_name="Linha",
                                    on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_GRUPO = models.ForeignKey(GRUPO_PRODUTOS, db_column="CHAVE_GRUPO", verbose_name="Grupo",
                                    on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_UNIDADE = models.ForeignKey(UNIDADES, db_column="CHAVE_UNIDADE", verbose_name="Unidade",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    DESCRICAO = models.CharField("Descrição", max_length=120, null=True, blank=True)
    PESO_LIQUIDO = models.DecimalField("Peso Liquido", max_digits=8, decimal_places=4, null=True, blank=True)
    PESO_BRUTO = models.DecimalField("Peso Bruto", max_digits=8, decimal_places=4, null=True, blank=True)
    FORA_DE_LINHA = models.CharField("Fora de Linha", max_length=3, null=True, blank=True)
    CODIGO_BARRA = models.CharField("Codigo de Barras (EAN13)", max_length=13, null=True, blank=True)
    CARACTERISTICA2 = models.CharField("Caracteristica 2", max_length=4000, null=True, blank=True)
    CHAVE_MARCA = models.ForeignKey(MARCAS, db_column="CHAVE_MARCA", verbose_name="Marca",
                                    on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(TIPO_PRODUTOS, db_column="CHAVE_TIPO", verbose_name="Tipo",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    def get_produto(self):
        Produtos = apps.get_model('home', 'Produtos')

        produto = Produtos.objects.filter(chave_analysis=self.pk).first()
        return produto

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

    @classmethod
    def get_status_fechado(cls):
        return cls.objects.filter(DESCRICAO='FECHADO').first()


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
        quantidade_tipos = clientes_ativos.values(SEGMENTO=F('CHAVE_TIPO__DESCRICAO')).annotate(
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
            quantidade = CLIENTES_HISTORICO.filter_em_aberto().filter(CHAVE_CLIENTE__in=clientes).count()
        return quantidade

    @property
    def quantidade_eventos_em_atraso(self):
        clientes = self.clientes.all()  # type:ignore
        quantidade = 0
        if clientes:
            quantidade = CLIENTES_HISTORICO.filter_em_atraso().filter(CHAVE_CLIENTE__in=clientes).count()
        return quantidade

    @property
    def ultimo_orcamento_aberto(self):
        clientes = self.clientes.all()  # type:ignore
        orcamentos = ORCAMENTOS.filter_com_valor_comercial_nao_registro_oportunidade().filter(
            CHAVE_CLIENTE__in=clientes
        )
        ultimo_orcamento = orcamentos.aggregate(ULTIMO_ORCAMENTO=Max('DATA_PEDIDO'))
        return ultimo_orcamento.get('ULTIMO_ORCAMENTO')

    @property
    def ultimo_pedido(self):
        clientes = self.clientes.all()  # type:ignore
        pedidos = PEDIDOS.filter_com_valor_comercial().filter(CHAVE_CLIENTE__in=clientes)
        ultimo_pedido = pedidos.aggregate(ULTIMO_PEDIDO=Max('DATA_PEDIDO'))
        return ultimo_pedido.get('ULTIMO_PEDIDO')

    @property
    def media_dias_orcamento_para_pedido(self):
        clientes = self.clientes.all()  # type:ignore
        pedidos = PEDIDOS.filter_com_valor_comercial().filter(CHAVE_CLIENTE__in=clientes,
                                                              DATA_PEDIDO__gte=data_inicio_analysis())
        dias = pedidos.values(DIAS_PARA_PEDIDO=F('DATA_PEDIDO') - F('CHAVE_ORCAMENTO__DATA_PEDIDO')).aggregate(
            MEDIA_DIAS_PARA_PEDIDO=Avg('DIAS_PARA_PEDIDO'))
        dias = dias.get('MEDIA_DIAS_PARA_PEDIDO')
        if not dias:
            return None
        return dias.days  # type:ignore

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
    CEP = models.CharField("CEP", max_length=9, null=True, blank=True)
    CGC = models.CharField("CNPJ / CPF", max_length=18, null=True, blank=True)
    CHAVE_TIPO = models.ForeignKey(CLIENTES_TIPOS, db_column="CHAVE_TIPO", verbose_name="Tipo de Cliente",
                                   on_delete=models.PROTECT, related_name="%(class)s_uf", null=True, blank=True)
    CHAVE_GRUPOECONOMICO = models.ForeignKey(GRUPO_ECONOMICO, db_column="CHAVE_GRUPOECONOMICO",
                                             verbose_name="Grupo Economico", on_delete=models.PROTECT,
                                             related_name="%(class)s", null=True, blank=True)
    TIPO = models.CharField("Natureza", max_length=20, null=True, blank=True)

    @classmethod
    def get_cgc_digitos(cls, cgc: str | int):
        """Filtra CNPJ / CPF usando somente digitos.

        Parametros:
        :cgc [str | int]: com o CNPJ / CPF, pode enviar com a formatação ou somente os digitos.

        Retorno:
        --------
        :CLIENTE | None: com o primeiro cliente encontrado."""
        cgc_digitos = somente_digitos(str(cgc))
        cliente = cls.objects.annotate(CGC_DIGITOS=RawSQL(
            "REGEXP_REPLACE(CGC, '[^0-9]', '')", [])).filter(CGC_DIGITOS=cgc_digitos).first()
        return cliente

    def __str__(self):
        return self.NOMERED


class CONTATOS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."CONTATOS"'
        verbose_name = 'Contato de Cliente'
        verbose_name_plural = 'Contatos de Cliente'
        permissions = [('export_contatosemails', 'Can export Contatos e-mails')]

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_CLIENTE = models.ForeignKey(CLIENTES, db_column="CHAVE_CLIENTE", verbose_name="Cliente",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    NOME = models.CharField("Nome", max_length=50, null=True, blank=True)
    AREA = models.CharField("Area", max_length=25, null=True, blank=True)
    FONEC = models.CharField("Fone 1", max_length=20, null=True, blank=True)
    DATA_NASC = models.DateField("Data Nascimento", auto_now=False, auto_now_add=False, null=True, blank=True)
    EMAIL = models.CharField("e-mail", max_length=100, null=True, blank=True)
    OBSERVACOES = models.CharField("Observações", max_length=100, null=True, blank=True)
    ENVIAR_MALA = models.CharField("Enviar Mala", max_length=3, null=True, blank=True)
    ATIVO = models.CharField("Ativo", max_length=3, null=True, blank=True)
    CELULAR = models.CharField("Celular", max_length=20, null=True, blank=True)
    GENERO = models.CharField("Genero", max_length=1, null=True, blank=True)

    def __str__(self):
        return self.NOME


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

    @classmethod
    def filter_em_aberto(cls):
        return cls.objects.filter(DATA_REALIZADO__isnull=True)

    @classmethod
    def filter_em_atraso(cls):
        return cls.filter_em_aberto().filter(DATA__lt=hoje())

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

    @classmethod
    def filter_com_valor_comercial_nao_registro_oportunidade(cls):
        return cls.objects.filter(CHAVE_TIPO__VALOR_COMERCIAL='SIM', REGISTRO_OPORTUNIDADE='NAO')

    def __str__(self):
        return f'{self.NUMPED}'


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
    CHAVE_ORCAMENTO = models.ForeignKey(ORCAMENTOS, db_column="CHAVE_ORCAMENTO", verbose_name="Orçamento",
                                        on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
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

    @classmethod
    def filter_com_valor_comercial(cls):
        return cls.objects.filter(CHAVE_TIPO__VALOR_COMERCIAL='SIM')

    def __str__(self):
        return f'{self.NUMPED}'


class PEDIDOS_ITENS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."PEDIDOS_ITENS"'
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Itens de Pedido'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_PEDIDO = models.ForeignKey(PEDIDOS, db_column="CHAVE_PEDIDO", verbose_name="Orçamento",
                                     on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_PRODUTO = models.ForeignKey(PRODUTOS, db_column="CHAVE_PRODUTO", verbose_name="Produto",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    QUANTIDADE = models.DecimalField("Quantidade", max_digits=22, decimal_places=6, null=True, blank=True)
    DATA_ENTREGA = models.DateField("Data de Entrega", auto_now=False, auto_now_add=False, null=True, blank=True)
    PRECO_TABELA = models.DecimalField("Preço de Tabela", max_digits=22, decimal_places=6, null=True, blank=True)
    PRECO_VENDA = models.DecimalField("Preço de Venda", max_digits=22, decimal_places=6, null=True, blank=True)
    VALOR_TOTAL = models.DecimalField("Valor Total", max_digits=22, decimal_places=6, null=True, blank=True)
    STATUS = models.CharField("Status", max_length=15, null=True, blank=True)
    RATEIO_FRETE = models.DecimalField("Rateio Frete", max_digits=22, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f'{self.CHAVE_PEDIDO} - {self.CHAVE_PRODUTO}'


class NOTAS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."NOTAS"'
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_JOB = models.ForeignKey(JOBS, db_column="CHAVE_JOB", verbose_name="Job", on_delete=models.PROTECT,
                                  related_name="%(class)s", null=True, blank=True)
    NF = models.IntegerField("Nº Nota")
    CHAVE_CLIENTE = models.ForeignKey(CLIENTES, db_column="CHAVE_CLIENTE", verbose_name="Cliente",
                                      on_delete=models.PROTECT, related_name="%(class)s_chave_cliente", null=True,
                                      blank=True)
    ESPECIE = models.CharField("Especie", max_length=1, null=True, blank=True)
    DATA_EMISSAO = models.DateField("Data Emissão", auto_now=False, auto_now_add=False, null=True, blank=True)
    VALOR_FRETE = models.DecimalField("Valor Frete", max_digits=22, decimal_places=6, null=True, blank=True)
    VALOR_MERCADORIAS = models.DecimalField("Valor Mercadorias", max_digits=22, decimal_places=6, null=True,
                                            blank=True)
    ATIVA = models.CharField("Ativa", max_length=3, null=True, blank=True)
    VALOR_COMERCIAL = models.CharField("Valor Comercial", max_length=3, null=True, blank=True)
    VALOR_FRETE_EMPRESA = models.DecimalField("Valor Frete Empresa", max_digits=22, decimal_places=6, null=True,
                                              blank=True)
    FRETE_INCL_ITEM = models.CharField("Frete Incluso nos Itens", max_length=3, null=True, blank=True)
    VALOR_FRETE_INCL_ITEM = models.DecimalField("Valor Frete Incluso nos Itens", max_digits=22, decimal_places=6,
                                                null=True, blank=True)
    NFE_NAC = models.CharField("NF-e Nacional", max_length=3, null=True, blank=True)

    @classmethod
    def filter_com_valor_comercial(cls):
        return cls.objects.filter(VALOR_COMERCIAL='SIM')

    def __str__(self):
        return f'{self.NF}'


class NOTAS_ITENS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."NOTAS_ITENS"'
        verbose_name = 'Item da Nota'
        verbose_name_plural = 'Itens da Nota'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_NOTA = models.ForeignKey(NOTAS, db_column="CHAVE_NOTA", verbose_name="Nota",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    NUMPED = models.ForeignKey(PEDIDOS_ITENS, db_column="NUMPED", verbose_name="Item de Pedido",
                               on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_PRODUTO = models.ForeignKey(PRODUTOS, db_column="CHAVE_PRODUTO", verbose_name="Produto",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    QUANTIDADE = models.DecimalField("Quantidade", max_digits=22, decimal_places=6, null=True, blank=True)
    PRECO_TABELA = models.DecimalField("Preço de Tabela", max_digits=22, decimal_places=6, null=True, blank=True)
    PRECO_FATURADO = models.DecimalField("Preço Faturado", max_digits=22, decimal_places=6, null=True, blank=True)
    VALOR_MERCADORIAS = models.DecimalField("Valor Mercadorias", max_digits=22, decimal_places=6, null=True,
                                            blank=True)
    RATEIO_FRETE = models.DecimalField("Rateio Frete", max_digits=22, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f'{self.CHAVE_NOTA} - {self.CHAVE_PRODUTO}'


class NOTAS_NFE_LOG(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."NOTAS_NFE_LOG"'
        verbose_name = 'Log NFe Nota'
        verbose_name_plural = 'Logs NFe Notas'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_NOTA = models.ForeignKey(NOTAS, db_column="CHAVE_NOTA", verbose_name="Nota",
                                   on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    DESCRICAO = models.CharField("Descrição", max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.CHAVE_NOTA} - {self.DESCRICAO}'


class INFORMACOES_CLI(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."INFORMACOES_CLI"'
        verbose_name = 'Informação Estrategica'
        verbose_name_plural = 'Informações Estrategicas'

    CHAVE = models.IntegerField("ID", primary_key=True)
    DESCRICAO = models.CharField("Descrição", max_length=100, null=True, blank=True)

    def __str__(self):
        return self.DESCRICAO


class FORNECEDORES(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."FORNECEDORES"'
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'

    CODFOR = models.IntegerField("ID", primary_key=True)
    NOMERED = models.CharField("Nome Reduzido", max_length=20, null=True, blank=True)
    NOME = models.CharField("Razão Social", max_length=50, null=True, blank=True)

    def get_fornecedor(self):
        Fornecedores = apps.get_model('home', 'Fornecedores')

        fornecedor = Fornecedores.objects.filter(chave_analysis=self.pk).first()
        return fornecedor

    @property
    def sigla(self):
        fornecedor = self.get_fornecedor()
        if not fornecedor:
            return ''
        return fornecedor.sigla  # type:ignore

    sigla.fget.short_description = 'Sigla'  # type:ignore

    def __str__(self):
        return self.NOMERED


class OC_MP(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."OC_MP"'
        verbose_name = 'Ordem de Compra'
        verbose_name_plural = 'Ordens de Compra'

    CHAVE = models.IntegerField("ID", primary_key=True)
    CHAVE_FORNECEDOR = models.ForeignKey(FORNECEDORES, db_column="CHAVE_FORNECEDOR", verbose_name="Fornecedor",
                                         on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    CHAVE_JOB = models.ForeignKey(JOBS, db_column="CHAVE_JOB", verbose_name="Job", on_delete=models.PROTECT,
                                  related_name="%(class)s", null=True, blank=True)
    DATA_EMISSAO = models.DateField("Data Emissão", auto_now=False, auto_now_add=False, null=True, blank=True)

    def __str__(self):
        return str(self.CHAVE)


class OC_MP_ITENS(ReadOnlyMixin, models.Model):
    class Meta:
        managed = False
        db_table = '"COPLAS"."OC_MP_ITENS"'
        verbose_name = 'Ordem de Compra Item'
        verbose_name_plural = 'Ordem de Compra Itens'

    CHAVE = models.IntegerField("ID", primary_key=True)
    ID_ITEM = models.IntegerField("ID Item")
    CHAVE_OC = models.ForeignKey(OC_MP, db_column="CHAVE_OC", verbose_name="Ordem de Compra", on_delete=models.PROTECT,
                                 related_name="%(class)s", null=True, blank=True)
    CHAVE_MATERIAL = models.ForeignKey(PRODUTOS, db_column="CHAVE_MATERIAL", verbose_name="Material",
                                       on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)
    QUANTIDADE = models.DecimalField("Quantidade", max_digits=22, decimal_places=6, null=True, blank=True)
    DATA_ENTREGA = models.DateField("Data Entrega", auto_now=False, auto_now_add=False, null=True, blank=True)
    CHAVE_UNIDADE = models.ForeignKey(UNIDADES, db_column="CHAVE_UNIDADE", verbose_name="Unidade",
                                      on_delete=models.PROTECT, related_name="%(class)s", null=True, blank=True)

    @property
    def data_entrega_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.DATA_ENTREGA)

    data_entrega_as_ddmmyyyy.fget.short_description = 'Data Entrega'  # type:ignore

    def __str__(self):
        return str(self.CHAVE)
