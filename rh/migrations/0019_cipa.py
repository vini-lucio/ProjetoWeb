# Generated by Django 5.1 on 2024-11-12 18:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0018_horariosfuncionarios'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cipa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado Em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado Em')),
                ('integrante_cipa_inicio', models.DateField(verbose_name='Integrante CIPA Inicio')),
                ('integrante_cipa_fim', models.DateField(verbose_name='Integrante CIPA Fim')),
                ('estabilidade_inicio', models.DateField(verbose_name='Estabilidade Inicio')),
                ('estabilidade_fim', models.DateField(verbose_name='Estabilidade Fim')),
                ('atualizado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_atualizado_por', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado Por')),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_criado_por', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por')),
                ('funcionario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='rh.funcionarios', verbose_name='Funcionario')),
            ],
            options={
                'verbose_name': 'CIPA',
                'verbose_name_plural': 'CIPA',
            },
        ),
    ]
