# Generated by Django 5.1 on 2024-12-18 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0047_alter_produtosmodelostags_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='produtosmodelos',
            name='slug',
            field=models.SlugField(blank=True, null=True, verbose_name='Slug'),
        ),
        migrations.AddField(
            model_name='produtosmodelostags',
            name='slug',
            field=models.SlugField(blank=True, null=True, verbose_name='Slug'),
        ),
    ]
