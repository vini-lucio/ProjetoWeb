# Generated by Django 5.1 on 2024-10-15 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0018_remove_homelinks_homelinks_unique_titulo_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='homelinks',
            constraint=models.UniqueConstraint(fields=('titulo',), name='homelinks_unique_titulo', violation_error_message='Titulo é campo unico'),
        ),
        migrations.AddConstraint(
            model_name='homelinks',
            constraint=models.UniqueConstraint(fields=('slug',), name='homelinks_unique_slug', violation_error_message='Slug é campo unico'),
        ),
    ]
