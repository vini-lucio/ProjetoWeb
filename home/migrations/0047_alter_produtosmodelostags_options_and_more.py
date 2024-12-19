# Generated by Django 5.1 on 2024-12-18 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0046_alter_produtosmodelos_tags'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='produtosmodelostags',
            options={'ordering': ('descricao',), 'verbose_name': 'Produtos Modelos Tag', 'verbose_name_plural': 'Produtos Modelos Tags'},
        ),
        migrations.AlterModelOptions(
            name='produtosmodelostopicos',
            options={'ordering': ('ordem',), 'verbose_name': 'Produtos Modelos Topico', 'verbose_name_plural': 'Produtos Modelos Topicos'},
        ),
        migrations.AddField(
            model_name='produtosmodelostopicos',
            name='ordem',
            field=models.IntegerField(default=10, verbose_name='Ordem'),
        ),
        migrations.AlterField(
            model_name='produtosmodelostopicos',
            name='conteudo',
            field=models.TextField(verbose_name='Conteudo'),
        ),
    ]