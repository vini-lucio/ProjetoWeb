# Generated by Django 5.1 on 2025-02-18 18:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0064_regioes'),
    ]

    operations = [
        migrations.AddField(
            model_name='estados',
            name='regiao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='home.regioes', verbose_name='Região'),
        ),
    ]
