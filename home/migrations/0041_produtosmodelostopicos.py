# Generated by Django 5.1 on 2024-12-17 15:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0040_produtosmodelos_atualizado_em_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProdutosModelosTopicos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100, verbose_name='Titulo')),
                ('conteudo', models.TextField(verbose_name='Conteudo')),
                ('modelo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s', to='home.produtosmodelos', verbose_name='Modelo')),
            ],
            options={
                'verbose_name': 'Produtos Modelos Topico',
                'verbose_name_plural': 'Produtos Modelos Topicos',
            },
        ),
    ]