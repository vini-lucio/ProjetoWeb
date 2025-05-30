# Generated by Django 5.1 on 2025-04-09 13:19

import utils.base_models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0018_pedidos'),
    ]

    operations = [
        migrations.CreateModel(
            name='CONTATOS',
            fields=[
                ('CHAVE', models.IntegerField(primary_key=True, serialize=False, verbose_name='ID')),
                ('NOME', models.CharField(blank=True, max_length=50, null=True, verbose_name='Nome')),
                ('AREA', models.CharField(blank=True, max_length=25, null=True, verbose_name='Area')),
                ('FONEC', models.CharField(blank=True, max_length=20, null=True, verbose_name='Fone 1')),
                ('DATA_NASC', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('EMAIL', models.CharField(blank=True, max_length=100, null=True, verbose_name='e-mail')),
                ('OBSERVACOES', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observações')),
                ('ENVIAR_MALA', models.CharField(blank=True, max_length=3, null=True, verbose_name='Enviar Mala')),
                ('ATIVO', models.CharField(blank=True, max_length=3, null=True, verbose_name='Ativo')),
                ('CELULAR', models.CharField(blank=True, max_length=20, null=True, verbose_name='Celular')),
                ('GENERO', models.CharField(blank=True, max_length=1, null=True, verbose_name='Genero')),
            ],
            options={
                'verbose_name': 'Contato de Cliente',
                'verbose_name_plural': 'Contatos de Cliente',
                'db_table': '"COPLAS"."CONTATOS"',
                'permissions': [('export_contatosemails', 'Can export Contatos e-mails')],
                'managed': False,
            },
            bases=(utils.base_models.ReadOnlyMixin, models.Model),
        ),
    ]
