# Generated by Django 5.1 on 2024-10-15 18:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0017_alter_homelinks_slug_alter_homelinks_titulo'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='homelinks',
            name='homelinks_unique_titulo',
        ),
        migrations.RemoveConstraint(
            model_name='homelinks',
            name='homelinks_unique_slug',
        ),
    ]
