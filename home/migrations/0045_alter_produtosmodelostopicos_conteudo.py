# Generated by Django 5.1 on 2024-12-17 20:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0044_produtosmodelos_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produtosmodelostopicos',
            name='conteudo',
            field=models.TextField(blank=True, default='', verbose_name='Conteudo'),
        ),
    ]