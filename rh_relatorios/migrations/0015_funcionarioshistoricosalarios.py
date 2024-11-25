# Generated by Django 5.1 on 2024-11-25 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0014_historico_salarios_view'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuncionariosHistoricoSalarios',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('job', models.CharField(blank=True, max_length=30, null=True, verbose_name='Job')),
                ('nome', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nome')),
                ('data_entrada', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('data_salario', models.DateField(blank=True, null=True, verbose_name='Data Salario')),
                ('setor', models.CharField(blank=True, max_length=50, null=True, verbose_name='Setor')),
                ('funcao', models.CharField(blank=True, max_length=70, null=True, verbose_name='Função')),
                ('motivo', models.CharField(blank=True, max_length=30, null=True, verbose_name='Motivo')),
                ('modalidade', models.CharField(blank=True, max_length=20, null=True, verbose_name='Modalidade')),
                ('salario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Salario')),
                ('salario_convertido', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Salario Convertido (*220h)')),
                ('comissao_carteira', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Carteira %')),
                ('comissao_dupla', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Dupla %')),
                ('comissao_geral', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Geral %')),
                ('observacoes', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observações')),
            ],
            options={
                'verbose_name': 'Relatorio Funcionario Historico de Salarios',
                'verbose_name_plural': 'Relatorio Funcionarios Historico de Salarios',
                'db_table': 'rh_historico_salarios_view',
                'managed': False,
            },
        ),
    ]
