# Generated by Django 5.1 on 2024-10-31 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0025_jobs'),
    ]

    operations = [
        migrations.CreateModel(
            name='Paises',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chave_analysis', models.IntegerField(verbose_name='ID Analysis')),
                ('nome', models.CharField(max_length=30, verbose_name='Descrição')),
                ('chave_migracao', models.IntegerField(null=True, verbose_name='Chave Migração')),
            ],
            options={
                'verbose_name': 'País',
                'verbose_name_plural': 'Países',
                'constraints': [models.UniqueConstraint(fields=('nome',), name='paises_unique_nome', violation_error_message='Nome é unico em Países')],
            },
        ),
    ]
