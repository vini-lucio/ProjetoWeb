# Generated by Django 5.1 on 2025-02-21 11:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frete', '0016_alter_transportadorasregioesvalores_arquivo_migrar_cidades'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transportadorasregioesmargens',
            options={'ordering': ('transportadora_regiao_valor__transportadora_origem_destino', 'transportadora_regiao_valor__descricao', 'ate_kg'), 'verbose_name': 'Transportadoras Região Margem', 'verbose_name_plural': 'Transportadoras Região Margens'},
        ),
    ]
