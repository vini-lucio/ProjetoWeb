# Generated by Django 5.1 on 2025-01-15 12:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0056_remove_estadosicms_chave_migracao'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='estadosicms',
            options={'ordering': ('uf_origem__sigla', 'uf_destino__sigla'), 'verbose_name': 'Estado ICMS', 'verbose_name_plural': 'Estados ICMS'},
        ),
    ]
