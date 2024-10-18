# Generated by Django 5.1 on 2024-10-15 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_homelinks_homelinks_check_url_externo'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='homelinks',
            name='homelinks_check_url_externo',
        ),
        migrations.AddConstraint(
            model_name='homelinks',
            constraint=models.CheckConstraint(condition=models.Q(('link_externo', True), ('link_externo', False), _connector='OR'), name='homelinks_check_url_externo', violation_error_message='Informar URL do Link Externo'),
        ),
    ]