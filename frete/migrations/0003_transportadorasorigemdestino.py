# Generated by Django 5.1 on 2025-01-14 18:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frete', '0002_transportadoras_chave_migracao'),
        ('home', '0056_remove_estadosicms_chave_migracao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TransportadorasOrigemDestino',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Criado Em')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Atualizado Em')),
                ('atualizado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_atualizado_por', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado Por')),
                ('criado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_criado_por', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por')),
                ('estado_origem_destino', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='home.estadosicms', verbose_name='UF Origem - Destino ')),
                ('transportadora', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='frete.transportadoras', verbose_name='Transportadora')),
            ],
            options={
                'verbose_name': 'Transportadoras UF Origem / Destino',
                'verbose_name_plural': 'Transportadoras UF Origem / Destino',
                'constraints': [models.UniqueConstraint(fields=('transportadora', 'estado_origem_destino'), name='transportadorasorigemdestino_unique_origem_destino', violation_error_message='Transportadora, Origem e Destino são campos unicos')],
            },
        ),
    ]
