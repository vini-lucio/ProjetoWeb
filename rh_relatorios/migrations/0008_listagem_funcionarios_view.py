# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0007_salario_funcao_atual_view'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW rh_listagem_funcionarios_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome,
                    rh_salario_funcao_atual_view.funcao,
                    rh_funcionarios.sexo,
                    rh_funcionarios.data_nascimento,
                    rh_funcionarios.rg,
                    CASE WHEN cipa_atual.funcionario_id IS NOT NULL THEN TRUE ELSE FALSE END AS membro_cipa

                FROM
                    rh_funcionarios
                    INNER JOIN home_jobs ON rh_funcionarios.job_id = home_jobs.id
                    LEFT JOIN rh_salario_funcao_atual_view ON rh_funcionarios.id = rh_salario_funcao_atual_view.funcionario_id
                    LEFT JOIN (
                        SELECT DISTINCT
                            rh_cipa.funcionario_id

                        FROM
                            rh_cipa

                        WHERE
                            CURRENT_DATE >= rh_cipa.integrante_cipa_inicio AND
                            CURRENT_DATE <= rh_cipa.integrante_cipa_fim
                    ) cipa_atual ON rh_funcionarios.id = cipa_atual.funcionario_id

                WHERE
                    rh_funcionarios.data_saida IS NULL;
            """,
            """
            DROP VIEW rh_listagem_funcionarios_view;
            """
        ),
    ]
