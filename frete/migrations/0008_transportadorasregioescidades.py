# Generated by Django 5.1 on 2025-01-17 17:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frete', '0007_transportadorasregioesmargens'),
        ('home', '0057_alter_estadosicms_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TransportadorasRegioesCidades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado Em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado Em')),
                ('prazo_tipo', models.CharField(blank=True, choices=[('DIAS', 'Dias'), ('DIAS UTEIS', 'Dias Uteis')], max_length=10, null=True, verbose_name='Prazo Tipo')),
                ('prazo', models.IntegerField(default=0, verbose_name='Prazo')),
                ('frequencia', models.CharField(blank=True, max_length=100, null=True, verbose_name='Frequencia')),
                ('observacoes', models.CharField(blank=True, max_length=100, null=True, verbose_name='Observações')),
                ('taxa', models.DecimalField(decimal_places=2, default=0, max_digits=9, verbose_name='Taxa (R$)')),
                ('cif', models.BooleanField(default=False, verbose_name='Frete CIF')),
                ('atualizado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_atualizado_por', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado Por')),
                ('cidade', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='home.cidades', verbose_name='Cidade')),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_criado_por', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por')),
                ('transportadora_regiao_valor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s', to='frete.transportadorasregioesvalores', verbose_name='Transportadora Região')),
            ],
            options={
                'verbose_name': 'Transportadoras Região Cidade',
                'verbose_name_plural': 'Transportadoras Região Cidades',
                'constraints': [models.UniqueConstraint(fields=('transportadora_regiao_valor', 'cidade'), name='transportadorasresgioescidades_unique_cidade', violation_error_message='Transportadora Região e Cidade são campos unicos')],
            },
        ),
    ]
