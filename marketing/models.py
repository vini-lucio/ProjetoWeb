from django.db import models
from django.utils import timezone
from datetime import datetime
from rh.models import Funcionarios
from utils.converter import converter_data_django_para_str_ddmmyyyy


class LeadsRdStation(models.Model):
    class Meta:
        verbose_name = 'Lead RD Station'
        verbose_name_plural = 'Leads RD Station'
        constraints = [
            models.UniqueConstraint(
                fields=['empresa',],
                name='leadsrdstation_unique_empresa',
                violation_error_message="Empresa é unico em Leads RD Station"
            ),
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='leadsrdstation_unique_chave_analysis',
                violation_error_message="ID Cliente Analysis é unico em Leads RD Station"
            ),
        ]

    chave_analysis = models.IntegerField("ID Cliente Analysis", blank=True, null=True)
    dados_bruto = models.TextField("Dados Bruto", blank=True, null=True)
    identificador = models.CharField("Identificador", max_length=100, blank=True, null=True)
    criado_em = models.DateTimeField("Criado Em", auto_now=False, auto_now_add=False, blank=True, null=True)
    conversion_url = models.CharField("URL de Conversão", max_length=1000, blank=True, null=True)
    conversion_domain = models.CharField("Dominio de Conversão", max_length=100, blank=True, null=True)
    email_lead = models.EmailField("e-mail", max_length=254, blank=True, null=True)
    cnpj = models.CharField("CNPJ", max_length=20, blank=True, null=True)
    user_agent = models.CharField("User Agent", max_length=1000, blank=True, null=True)
    device = models.CharField("Dispositivo", max_length=100, blank=True, null=True)
    asset_id = models.IntegerField("ID Asset", blank=True, null=True)
    conversion_payload = models.CharField("Payload de Conversão", max_length=1000, blank=True, null=True)
    empresa = models.CharField("Empresa", max_length=100, blank=True, null=True)
    nome = models.CharField("Nome", max_length=100, blank=True, null=True)
    telefone = models.CharField("Telefone", max_length=100, blank=True, null=True)
    origem = models.CharField("Origem", max_length=100, blank=True, null=True)
    interesse = models.CharField("Interesse", max_length=100, blank=True, null=True)
    mensagem = models.TextField("Mensagem", blank=True, null=True)
    lead_valido = models.BooleanField("Lead Valido", default=True)
    observacoes = models.CharField("Observações", max_length=100, blank=True, null=True)
    responsavel = models.ForeignKey(Funcionarios, verbose_name="Responsavel", on_delete=models.PROTECT,
                                    related_name="%(class)s", null=True, blank=True)

    map_nomes_alternativos_campos = {
        'post_id': 'asset_id',
        'form_fields_field_1984dff': 'nome',
        'form_fields_field_a7cef9f': 'telefone',
        'form_fields_field_542bd78': 'empresa',
        'form_fields_field_53e54fe': 'interesse',
        'form_fields_field_5bbe7d8': 'mensagem',
        'form_fields_field_4476bfc': 'mensagem',
        'form_fields_field_0864fd3': 'cnpj',
        'form_url': 'conversion_url',
    }

    @property
    def criado_em_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.criado_em.date()) if self.criado_em else ''

    criado_em_as_ddmmyyyy.fget.short_description = 'Criado Em'  # type:ignore

    @property
    def responsavel_nome(self):
        return self.responsavel.nome if self.responsavel else ''

    responsavel_nome.fget.short_description = 'Responsavel'  # type:ignore

    def __str__(self) -> str:
        return str(self.pk) if self.pk else ''

    def clean(self) -> None:
        if not self.pk and self.dados_bruto:
            map_nomes_alternativos_campos = LeadsRdStation.map_nomes_alternativos_campos
            bruto = self.dados_bruto
            for linha in bruto.splitlines():
                if ':' in linha:
                    chave, valor = linha.split(':', 1)
                    chave = chave.strip().lower().replace(' ', '_')
                    valor = valor.strip()

                    if chave in map_nomes_alternativos_campos:
                        chave = map_nomes_alternativos_campos[chave]

                    if chave == 'criado_em':
                        data_hora = valor.replace(' às ', ' ')
                        data_hora = datetime.strptime(data_hora, "%d/%m/%Y %H:%M")
                        valor = data_hora

                    print(chave, valor)
                    setattr(self, chave, valor)

        if not self.criado_em:
            self.criado_em = timezone.now()

        return super().clean()
