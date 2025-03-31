# Generated by Django 5.1 on 2025-03-28 19:54

import utils.base_models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0013_status_orcamentos_itens'),
    ]

    operations = [
        migrations.CreateModel(
            name='CLIENTES',
            fields=[
                ('CODCLI', models.IntegerField(primary_key=True, serialize=False, verbose_name='ID')),
                ('NOMERED', models.CharField(blank=True, max_length=20, null=True, verbose_name='Nome Reduzido')),
                ('STATUS', models.CharField(blank=True, max_length=1, null=True, verbose_name='Status')),
                ('CGC', models.CharField(blank=True, max_length=18, null=True, verbose_name='CNPJ / CPF')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': '"COPLAS"."CLIENTES"',
                'managed': False,
            },
            bases=(utils.base_models.ReadOnlyMixin, models.Model),
        ),
        migrations.CreateModel(
            name='GRUPO_ECONOMICO',
            fields=[
                ('CHAVE', models.IntegerField(primary_key=True, serialize=False, verbose_name='ID')),
                ('DESCRICAO', models.CharField(blank=True, max_length=50, null=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Grupo Economico',
                'verbose_name_plural': 'Grupos Economicos',
                'db_table': '"COPLAS"."GRUPO_ECONOMICO"',
                'managed': False,
            },
            bases=(utils.base_models.ReadOnlyMixin, models.Model),
        ),
    ]
