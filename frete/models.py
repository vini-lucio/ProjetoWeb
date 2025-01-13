from django.db import models
from utils.base_models import BaseLogModel
from utils.choices import status_ativo_inativo


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

    status_produtos = status_ativo_inativo

    chave_analysis = models.IntegerField("ID Analysis", default=0)
    nome = models.CharField("Nome", max_length=50)
    status = models.CharField("Status", max_length=10, default='ativo', choices=status_produtos)  # type:ignore
    simples_nacional = models.BooleanField("Simples Nacional", default=False)
    entrega_uf_diferente_faturamento = models.BooleanField("Entrega UF Diferente Faturamento", default=False)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.nome
