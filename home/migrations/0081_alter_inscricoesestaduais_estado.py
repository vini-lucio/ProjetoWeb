# Generated by Django 5.1 on 2025-07-30 10:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0080_alter_inscricoesestaduais_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscricoesestaduais',
            name='estado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='home.estados', verbose_name='Estado'),
        ),
    ]
