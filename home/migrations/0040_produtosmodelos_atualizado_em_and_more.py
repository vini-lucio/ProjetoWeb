# Generated by Django 5.1 on 2024-12-17 14:17

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0039_produtosmodelos'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='produtosmodelos',
            name='atualizado_em',
            field=models.DateTimeField(auto_now=True, verbose_name='Atualizado Em'),
        ),
        migrations.AddField(
            model_name='produtosmodelos',
            name='atualizado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_atualizado_por', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado Por'),
        ),
        migrations.AddField(
            model_name='produtosmodelos',
            name='criado_em',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Criado Em'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='produtosmodelos',
            name='criado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_criado_por', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por'),
        ),
    ]