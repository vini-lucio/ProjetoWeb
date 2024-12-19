# Generated by Django 5.1 on 2024-11-25 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0009_funcionarioslistagem'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuncionariosSalarioFuncaoAtual',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('job', models.CharField(blank=True, max_length=30, null=True, verbose_name='Job')),
                ('nome', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nome')),
                ('data_entrada', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('funcao', models.CharField(blank=True, max_length=70, null=True, verbose_name='Função')),
                ('salario', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Salario')),
                ('salario_convertido', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Salario Convertido (*220h)')),
                ('comissao_carteira', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Carteira %')),
                ('comissao_dupla', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Dupla %')),
                ('comissao_geral', models.DecimalField(decimal_places=4, max_digits=7, verbose_name='Comissão Geral %')),
            ],
            options={
                'verbose_name': 'Relatorio Funcionario Salario Função Atual',
                'verbose_name_plural': 'Relatorio Funcionarios Salario Função Atual',
                'db_table': 'rh_salario_funcao_atual_view',
                'managed': False,
            },
        ),
    ]