# Generated by Django 5.1 on 2025-01-09 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0053_sitesetup_medida_volume_padrao_x_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produtos',
            name='quantidade_volume',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=10, verbose_name='Quantidade Por Volume'),
        ),
    ]
