# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW rh_admissao_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.registro,
                    rh_funcionarios.nome,
                    EXTRACT(MONTH FROM rh_funcionarios.data_entrada) AS mes_entrada,
                    rh_funcionarios.data_entrada,
                    ROUND((CURRENT_DATE - rh_funcionarios.data_entrada) / 365.00, 1) AS tempo_casa_anos

                FROM
                    rh_funcionarios,
                    home_jobs

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_funcionarios.data_saida IS NULL;
            """,
            """
            DROP VIEW rh_admissao_view;
            """
        ),
    ]
