# Generated by Django 5.1 on 2024-11-05 17:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0002_dissidios'),
    ]

    operations = [
        migrations.AddField(
            model_name='dissidios',
            name='aplicado',
            field=models.BooleanField(default=False, verbose_name='Dissidio Aplicado?'),
        ),
    ]
