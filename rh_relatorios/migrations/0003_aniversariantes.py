# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0002_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW rh_aniversariantes_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome,
                    EXTRACT(MONTH FROM rh_funcionarios.data_nascimento) AS mes_nascimento,
                    rh_funcionarios.data_nascimento

                FROM
                    rh_funcionarios,
                    home_jobs

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_funcionarios.data_saida IS NULL;
            """,
            """
            DROP VIEW rh_aniversariantes_view;
            """
        ),
    ]
