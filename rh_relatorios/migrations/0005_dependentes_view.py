# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0004_aniversariantes'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW rh_dependentes_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome,
                    rh_funcionarios.sexo,
                    rh_dependentes.nome AS nome_dependente,
                    rh_dependentes.data_nascimento,
                    ROUND((CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00, 2) AS idade,
                    CASE WHEN (CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00 < 13 THEN TRUE ELSE FALSE END AS crianca

                FROM
                    rh_funcionarios,
                    home_jobs,
                    rh_dependentes

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_funcionarios.id = rh_dependentes.funcionario_id AND
                    rh_funcionarios.data_saida IS NULL AND
                    rh_dependentes.dependente_tipo_id IN (SELECT id FROM rh_dependentestipos WHERE descricao IN ('FILHO(A)', 'ENTEADO(A)'));
            """,
            """
            DROP VIEW rh_dependentes_view;
            """
        ),
    ]
