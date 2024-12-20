# Generated by Django 5.1 on 2024-11-13 16:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0021_valetransportesfuncionarios'),
    ]

    operations = [
        migrations.AlterField(
            model_name='valetransportes',
            name='dias',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Atenção! Alterar esse campo alterará todos os funcionarios ativos com essa linha e tipo', max_digits=3, verbose_name='Dias'),
        ),
        migrations.AlterField(
            model_name='valetransportes',
            name='quantidade_por_dia',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Atenção! Alterar esse campo alterará todos os funcionarios ativos com essa linha e tipo', max_digits=3, verbose_name='Quantidade por Dia'),
        ),
        migrations.AlterField(
            model_name='valetransportes',
            name='valor_unitario',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Atenção! Alterar esse campo alterará todos os funcionarios ativos com essa linha e tipo', max_digits=10, verbose_name='Valor Unitario R$'),
        ),
        migrations.AlterField(
            model_name='valetransportesfuncionarios',
            name='dias',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Preencher 0 para usar os dias do vale transporte', max_digits=3, verbose_name='Dias'),
        ),
        migrations.AlterField(
            model_name='valetransportesfuncionarios',
            name='quantidade_por_dia',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Preencher 0 para usar a quantidade por dia do vale transporte', max_digits=3, verbose_name='Quantidade por Dia'),
        ),
        migrations.AlterField(
            model_name='valetransportesfuncionarios',
            name='vale_transporte',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='rh.valetransportes', verbose_name='Vale Transporte'),
        ),
    ]
