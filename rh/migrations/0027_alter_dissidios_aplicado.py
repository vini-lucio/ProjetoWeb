# Generated by Django 5.1 on 2024-11-18 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0026_salarios'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dissidios',
            name='aplicado',
            field=models.BooleanField(default=False, help_text='ATENÇÃO, APLICAR DISSIDIO É IRREVERSIVEL!', verbose_name='Dissidio Aplicado?'),
        ),
    ]