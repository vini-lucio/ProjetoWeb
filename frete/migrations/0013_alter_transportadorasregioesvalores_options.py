# Generated by Django 5.1 on 2025-02-05 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('frete', '0012_alter_transportadorasregioesvalores_taxa_valor_nota_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transportadorasregioesvalores',
            options={'ordering': ('transportadora_origem_destino',), 'verbose_name': 'Transportadoras Região Valores', 'verbose_name_plural': 'Transportadoras Regiões Valores'},
        ),
    ]
