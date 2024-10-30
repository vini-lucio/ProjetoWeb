# Generated by Django 5.1 on 2024-10-25 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0022_alter_sitesetup_dias_uteis_mes'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssistentesTecnicos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Nome')),
                ('status', models.CharField(choices=[('ativo', 'Ativo'), ('inativo', 'Inativo')], default='ativo', max_length=30, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Assistente Tecnico',
                'verbose_name_plural': 'Assistentes Tecnicos',
                'constraints': [models.UniqueConstraint(fields=('nome',), name='assistente_unique_nome', violation_error_message='Nome é campo unico')],
            },
        ),
    ]