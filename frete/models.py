from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from utils.base_models import BaseLogModel
from utils.choices import status_ativo_inativo
from home.models import EstadosIcms, Cidades


class Transportadoras(BaseLogModel):
    class Meta:
        verbose_name = 'Transportadora'
        verbose_name_plural = 'Transportadoras'
        constraints = [
            models.UniqueConstraint(
                fields=['nome',],
                name='transportadoras_unique_nome',
                violation_error_message="Nome é campo unico"
            ),
        ]

    status_transportadoras = status_ativo_inativo

    chave_analysis = models.IntegerField("ID Analysis", default=0)
    nome = models.CharField("Nome", max_length=50)
    status = models.CharField("Status", max_length=10, default='ativo', choices=status_transportadoras)  # type:ignore
    simples_nacional = models.BooleanField("Simples Nacional", default=False)
    entrega_uf_diferente_faturamento = models.BooleanField("Entrega UF Diferente Faturamento", default=False)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.nome


class TransportadorasOrigemDestino(BaseLogModel):
    class Meta:
        verbose_name = 'Transportadoras UF Origem / Destino'
        verbose_name_plural = 'Transportadoras UF Origem / Destino'
        constraints = [
            models.UniqueConstraint(
                fields=['transportadora', 'estado_origem_destino',],
                name='transportadorasorigemdestino_unique_origem_destino',
                violation_error_message="Transportadora, Origem e Destino são campos unicos"
            ),
        ]

    status_transportadoras_origem_destino = status_ativo_inativo

    transportadora = models.ForeignKey(Transportadoras, verbose_name="Transportadora", on_delete=models.PROTECT,
                                       related_name="%(class)s")
    estado_origem_destino = models.ForeignKey(EstadosIcms, verbose_name="UF Origem - Destino ",
                                              on_delete=models.PROTECT, related_name="%(class)s")
    status = models.CharField("Status", max_length=10, default='ativo',
                              choices=status_transportadoras_origem_destino)  # type:ignore

    def __str__(self) -> str:
        return f'{self.transportadora} / {self.estado_origem_destino}'


class TransportadorasRegioesValores(BaseLogModel):
    class Meta:
        verbose_name = 'Transportadoras Região Valores'
        verbose_name_plural = 'Transportadoras Regiões Valores'
        constraints = [
            models.UniqueConstraint(
                fields=['transportadora_origem_destino', 'descricao',],
                name='transportadorasresgioesvalores_unique_regiao',
                violation_error_message="Origem, Destino e descrição são campos unicos"
            ),
        ]

    status_transportadoras_regioes_valores = status_ativo_inativo
    prazo_tipos = {
        'DIAS': 'Dias',
        'DIAS UTEIS': 'Dias Uteis',
    }

    help_text_atendimento_cidades_especificas = "Desmarcar para considerar todas as cidades do estado de destino, desconsiderando as cidades especificadas em outras regiões da mesma transportadora"
    help_text_porcentagem_valor_nota = "Porcentagem sobre o valor da nota"
    help_text_valor_kg_excedente = "Marcar para considerar somente os kgs a mais do maior kg definido nas margens de kg"
    help_text_frete_peso = "Frete peso é o resultado final de acordo com os valores nas margens de kg e valor/kg"
    help_text_frete_minimo = "Valor a ser considerado quando a soma de todo custo de frete (liquido de ICMS) for menor que o informado"
    help_text_zona_rural = "Valor só é somado quando for selecionado zona rural no calculo do frete"

    transportadora_origem_destino = models.ForeignKey(TransportadorasOrigemDestino,
                                                      verbose_name="Transportadora / Origem - Destino",
                                                      on_delete=models.PROTECT, related_name="%(class)s")
    descricao = models.CharField("Descrição", max_length=50)
    atendimento_cidades_especificas = models.BooleanField("Atendimento Cidades Especificas", default=True,
                                                          help_text=help_text_atendimento_cidades_especificas)
    status = models.CharField("Status", max_length=10, default='ativo',
                              choices=status_transportadoras_regioes_valores)  # type:ignore
    razao = models.DecimalField("Razão (kg/m³)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    advaloren = models.DecimalField("Advaloren / Frete Valor (%)", max_digits=9, decimal_places=2,
                                    help_text=help_text_porcentagem_valor_nota, default=0)  # type:ignore
    advaloren_valor_minimo = models.DecimalField("Valor Minimo Advaloren / Frete Valor (R$)", max_digits=9,
                                                 decimal_places=2, default=0)  # type:ignore
    gris = models.DecimalField("Gris / Gerenciamento de Risco (%)", max_digits=9, decimal_places=2,
                               help_text=help_text_porcentagem_valor_nota, default=0)  # type:ignore
    gris_valor_minimo = models.DecimalField("Valor Minimo Gris / Gerenciamento de Risco (R$)", max_digits=9,
                                            decimal_places=2, default=0)  # type:ignore
    taxa_coleta = models.DecimalField("Taxa de Coleta (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    taxa_conhecimento = models.DecimalField("Taxa de Conhecimento (R$)", max_digits=9, decimal_places=2,
                                            default=0)  # type:ignore
    taxa_sefaz = models.DecimalField("Taxa Sefaz / TAS (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    taxa_suframa = models.DecimalField("Taxa Suframa (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    pedagio_fracao = models.DecimalField("Pedagio Fração (kg)", max_digits=9, decimal_places=2,
                                         default=0)  # type:ignore
    pedagio_valor_fracao = models.DecimalField("Pedagio Valor da Fração (R$)", max_digits=9, decimal_places=2,
                                               default=0)  # type:ignore
    pedagio_valor_minimo = models.DecimalField("Pedagio Valor Minimo (R$)", max_digits=9, decimal_places=2,
                                               default=0)  # type:ignore
    valor_kg = models.DecimalField("Valor/kg (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    valor_kg_excedente = models.BooleanField("Valor/kg Excedente", help_text=help_text_valor_kg_excedente,
                                             default=False)
    taxa_frete_peso = models.DecimalField("Outras Taxas sobre frete peso (%)", max_digits=9, decimal_places=2,
                                          help_text=help_text_frete_peso, default=0)  # type:ignore
    taxa_frete_peso_valor_minimo = models.DecimalField("Valor Minimo Outras Taxas sobre frete peso (R$)", max_digits=9,
                                                       decimal_places=2, default=0)  # type:ignore
    taxa_valor_nota = models.DecimalField("Outras Taxas sobre valor da nota (%)", max_digits=9,
                                          decimal_places=2, default=0)  # type:ignore
    taxa_valor_nota_valor_minimo = models.DecimalField(
        "Valor Minimo Outras Taxas sobre valor da nota (R$)", max_digits=9, decimal_places=2,
        default=0  # type:ignore
    )
    frete_minimo_valor = models.DecimalField("Frete Minimo (R$)", max_digits=9, decimal_places=2,
                                             help_text=help_text_frete_minimo, default=0)  # type:ignore
    frete_minimo_percentual = models.DecimalField("Frete Minimo sobre valor da nota (%)", max_digits=9,
                                                  decimal_places=2, help_text=help_text_frete_minimo,
                                                  default=0)  # type:ignore
    observacoes = models.CharField("Observações", max_length=100, null=True, blank=True)
    prazo_tipo = models.CharField("Prazo Tipo", max_length=10, null=True, blank=True,
                                  choices=prazo_tipos)  # type:ignore
    prazo_padrao = models.IntegerField("Prazo Padrão", default=0)
    frequencia_padrao = models.CharField("Frequencia Padrão", max_length=100, null=True, blank=True)
    observacoes_prazo_padrao = models.CharField("Observações Prazo Padrão", max_length=100, null=True, blank=True)
    atendimento_zona_rural = models.BooleanField("Atendimento Zona Rural", default=True)
    taxa_zona_rural = models.DecimalField("Taxa Zona Rural (R$)", max_digits=9, decimal_places=2,
                                          help_text=help_text_zona_rural, default=0)  # type:ignore

    def clean(self) -> None:
        super_clean = super().clean()

        try:
            if not self.atendimento_cidades_especificas:
                atendimeto_especifico = TransportadorasRegioesValores.objects.filter(
                    transportadora_origem_destino=self.transportadora_origem_destino,
                    atendimento_cidades_especificas=False
                ).exclude(id=self.pk).count()
                if atendimeto_especifico >= 1:
                    raise ValidationError(
                        {
                            'atendimento_cidades_especificas': 'Só é possivel ter uma região por transportadora na mesma origem e destino sem atendimento especifico de cidades'
                        }  # type:ignore
                    )
        except ObjectDoesNotExist:
            raise ValidationError(
                {'transportadora_origem_destino': "Transportadora / Origem - Destino é obrigatorio"}  # type:ignore
            )

        if self.prazo_padrao > 0 and not self.prazo_tipo:
            raise ValidationError({'prazo_tipo': 'Prazo Tipo precisa ser preenchido '})  # type:ignore

        if self.prazo_padrao == 0:
            self.prazo_tipo = None

        if not self.atendimento_zona_rural:
            self.taxa_zona_rural = 0

        return super_clean

    @classmethod
    def filter_ativos(cls):
        return cls.objects.filter(
            status='ativo',
            transportadora_origem_destino__status='ativo',
            transportadora_origem_destino__transportadora__status='ativo',
        )

    def __str__(self) -> str:
        return f'{self.transportadora_origem_destino} / {self.descricao}'


class TransportadorasRegioesMargens(BaseLogModel):
    class Meta:
        verbose_name = 'Transportadoras Região Margem'
        verbose_name_plural = 'Transportadoras Região Margens'
        constraints = [
            models.UniqueConstraint(
                fields=['transportadora_regiao_valor', 'ate_kg',],
                name='transportadorasresgioesmargens_unique_kg',
                violation_error_message="Transportadora Região e Até kg são campos unicos"
            ),
            models.CheckConstraint(
                check=Q(ate_kg__gt=0),
                name='transportadorasresgioesmargens_check_ate_kg',
                violation_error_message="Até kg precisa ser maior que 0"
            ),
            models.CheckConstraint(
                check=Q(valor__gt=0),
                name='transportadorasresgioesmargens_check_valor',
                violation_error_message="Valor precisa ser maior que 0"
            ),
        ]

    transportadora_regiao_valor = models.ForeignKey(TransportadorasRegioesValores, verbose_name="Transportadora Região",
                                                    on_delete=models.CASCADE, related_name="%(class)s")
    ate_kg = models.DecimalField("Até kg", max_digits=9, decimal_places=2, default=0)  # type:ignore
    valor = models.DecimalField("Valor (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore

    def __str__(self) -> str:
        return f'{self.transportadora_regiao_valor} / {self.ate_kg}'


class TransportadorasRegioesCidades(BaseLogModel):
    class Meta:
        verbose_name = 'Transportadoras Região Cidade'
        verbose_name_plural = 'Transportadoras Região Cidades'
        constraints = [
            models.UniqueConstraint(
                fields=['transportadora_regiao_valor', 'cidade',],
                name='transportadorasresgioescidades_unique_cidade',
                violation_error_message="Transportadora Região e Cidade são campos unicos"
            ),
        ]

    prazo_tipos = {
        'DIAS': 'Dias',
        'DIAS UTEIS': 'Dias Uteis',
    }

    transportadora_regiao_valor = models.ForeignKey(TransportadorasRegioesValores,
                                                    verbose_name="Transportadora Região Valor",
                                                    on_delete=models.CASCADE, related_name="%(class)s")
    cidade = models.ForeignKey(Cidades, verbose_name="Cidade", on_delete=models.PROTECT, related_name="%(class)s")
    prazo_tipo = models.CharField("Prazo Tipo", max_length=10, null=True, blank=True,
                                  choices=prazo_tipos)  # type:ignore
    prazo = models.IntegerField("Prazo", default=0)
    frequencia = models.CharField("Frequencia", max_length=100, null=True, blank=True)
    observacoes = models.CharField("Observações", max_length=100, null=True, blank=True)
    taxa = models.DecimalField("Taxa (R$)", max_digits=9, decimal_places=2, default=0)  # type:ignore
    cif = models.BooleanField("Frete CIF", default=False)

    def clean(self) -> None:
        super_clean = super().clean()

        try:
            if not self.transportadora_regiao_valor.atendimento_cidades_especificas:
                raise ValidationError(
                    {
                        'transportadora_regiao_valor': 'Transportadora Região Valor o atendimento não está especifico'
                    }  # type:ignore
                )
        except ObjectDoesNotExist:
            raise ValidationError(
                {'transportadora_regiao_valor': "Transportadora Região Valor é obrigatorio"}  # type:ignore
            )

        try:
            if self.cidade and self.transportadora_regiao_valor:
                uf_cidade = self.cidade.estado
                uf_transportadora_regiao = self.transportadora_regiao_valor.transportadora_origem_destino.estado_origem_destino.uf_destino
                if uf_cidade != uf_transportadora_regiao:
                    raise ValidationError(
                        {'cidade': 'UF da cidade é diferente do UF destino da região da transportadora'}  # type:ignore
                    )
        except ObjectDoesNotExist:
            raise ValidationError(
                {'transportadora_regiao_valor': "Transportadora Região Valor é obrigatorio",
                 'cidade': "Cidade é obrigatorio", }  # type:ignore
            )

        if self.prazo > 0 and not self.prazo_tipo:
            raise ValidationError({'prazo_tipo': 'Prazo Tipo precisa ser preenchido '})  # type:ignore

        if self.prazo == 0:
            self.prazo_tipo = None

        return super_clean

    def __str__(self) -> str:
        return f'{self.transportadora_regiao_valor} / {self.cidade.nome}'


# TODO: replicar valores
# TODO: importar/atualizar cidades prazos
# TODO: reajuste de valores
