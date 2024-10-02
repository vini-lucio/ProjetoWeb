# Generated by Django 5.1 on 2024-10-02 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_alter_homelinks_conteudo'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSetup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('favicon', models.ImageField(blank=True, help_text='A imagem será redimensionada para 32x32 px', null=True, upload_to='home/favicon/', verbose_name='Favicon')),
                ('logo_cabecalho', models.ImageField(blank=True, help_text='A imagem será redimensionada proporcionalmente para 100 px de altura', null=True, upload_to='home/logo/', verbose_name='Logo')),
                ('texto_rodape', models.TextField(blank=True, null=True, verbose_name='Texto do Rodapé')),
            ],
        ),
    ]