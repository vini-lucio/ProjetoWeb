# Generated by Django 5.1 on 2024-11-21 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('rh_relatorios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Admissoes',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('job', models.CharField(blank=True, max_length=30, null=True, verbose_name='Job')),
                ('registro', models.IntegerField(blank=True, null=True, verbose_name='Registro')),
                ('nome', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nome')),
                ('mes_entrada', models.DecimalField(blank=True, decimal_places=0, max_digits=2, null=True, verbose_name='Mes Entrada')),
                ('data_entrada', models.DateField(blank=True, null=True, verbose_name='Data Entrada')),
                ('tempo_casa_anos', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True, verbose_name='Tempo Casa Anos')),
            ],
            options={
                'verbose_name': 'Relatorio Admissão',
                'verbose_name_plural': 'Relatorio Admissões',
                'db_table': 'rh_admissao_view',
                'managed': False,
            },
        ),
    ]
