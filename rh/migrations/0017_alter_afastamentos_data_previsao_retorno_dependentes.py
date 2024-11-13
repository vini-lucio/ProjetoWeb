# Generated by Django 5.1 on 2024-11-12 12:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0016_alter_afastamentos_data_retorno'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='afastamentos',
            name='data_previsao_retorno',
            field=models.DateField(blank=True, null=True, verbose_name='Data Previsão Retorno'),
        ),
        migrations.CreateModel(
            name='Dependentes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado Em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado Em')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('data_nascimento', models.DateField(blank=True, null=True, verbose_name='Data Nascimento')),
                ('rg', models.CharField(blank=True, max_length=20, null=True, verbose_name='RG')),
                ('cpf', models.CharField(blank=True, max_length=14, null=True, verbose_name='CPF')),
                ('certidao_tipo', models.CharField(blank=True, choices=[('NASCIMENTO', 'Nascimento'), ('CASAMENTO', 'Casamento')], max_length=10, null=True, verbose_name='Certidão Tipo')),
                ('certidao_data_emissao', models.DateField(blank=True, null=True, verbose_name='Certidão Data Emissão')),
                ('certidao_termo_matricula', models.CharField(blank=True, max_length=32, null=True, verbose_name='Certidão Termo / Matricula')),
                ('certidao_livro', models.CharField(blank=True, max_length=5, null=True, verbose_name='Certidão Livro')),
                ('certidao_folha', models.CharField(blank=True, max_length=5, null=True, verbose_name='Certidão Folha')),
                ('dependente_ir', models.BooleanField(default=False, verbose_name='Dependente IR')),
                ('observacoes', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observações')),
                ('chave_migracao', models.IntegerField(blank=True, null=True, verbose_name='Chave Migração')),
                ('atualizado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_atualizado_por', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado Por')),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_criado_por', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por')),
                ('dependente_tipo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='rh.dependentestipos', verbose_name='Dependente Tipo')),
                ('funcionario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='rh.funcionarios', verbose_name='Funcionario')),
            ],
            options={
                'verbose_name': 'Dependente',
                'verbose_name_plural': 'Dependentes',
                'constraints': [models.UniqueConstraint(fields=('funcionario', 'dependente_tipo', 'nome'), name='dependentes_unique_dependente', violation_error_message='Nome e Tipo são unicos em Dependentes por Funcionario')],
            },
        ),
    ]