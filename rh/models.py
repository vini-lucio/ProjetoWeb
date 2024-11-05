from django.db import models


class Cbo(models.Model):
    class Meta:
        verbose_name = 'CBO'
        verbose_name_plural = 'CBO'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='cbo_unique_descricao',
                violation_error_message="Descrição é unico em CBO"
            ),
        ]

    numero = models.CharField("Numero", max_length=10)
    descricao = models.CharField("Descrição", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.numero} - {self.descricao}'
