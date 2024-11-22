# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0006_filhos12anos'),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP VIEW rh_filhos_12_anos_view;
            CREATE VIEW rh_filhos_12_anos_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome,
                    rh_dependentes.nome AS nome_dependente,
                    rh_dependentes.data_nascimento,
                    ROUND((CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00, 2) AS IDADE

                FROM
                    rh_funcionarios,
                    home_jobs,
                    rh_dependentes

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_funcionarios.id = rh_dependentes.funcionario_id AND
                    rh_funcionarios.data_saida IS NULL AND
                    rh_dependentes.dependente_tipo_id IN (SELECT id FROM rh_dependentestipos WHERE descricao IN ('FILHO(A)', 'ENTEADO(A)')) AND
                    (CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00 < 13;
            """,
            """
            DROP VIEW rh_filhos_12_anos_view;
            CREATE VIEW rh_filhos_12_anos_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome,
                    rh_dependentes.nome AS nome_dependente,
                    rh_dependentes.data_nascimento,
                    ROUND((CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00, 2) AS IDADE

                FROM
                    rh_funcionarios,
                    home_jobs,
                    rh_dependentes

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_funcionarios.id = rh_dependentes.funcionario_id AND
                    rh_funcionarios.data_saida IS NULL AND
                    rh_dependentes.dependente_tipo_id IN (4, 7) AND
                    (CURRENT_DATE - rh_dependentes.data_nascimento) / 365.00 < 13;
            """
        ),
    ]
