# Generated by Django 5.1 on 2024-11-06 17:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh', '0009_funcoes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='funcoes',
            name='atualizado_em',
        ),
        migrations.RemoveField(
            model_name='funcoes',
            name='atualizado_por',
        ),
        migrations.RemoveField(
            model_name='funcoes',
            name='criado_em',
        ),
        migrations.RemoveField(
            model_name='funcoes',
            name='criado_por',
        ),
    ]
