# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0034_jobs_razao_social'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE FUNCTION rateio_salario_adm_cp_ano_mes_a_mes(ano INT, mes INT)
            RETURNS TABLE (
                mes_i INT, total_salario NUMERIC, total_salario_mk NUMERIC, total_salario_cp NUMERIC, mk_percentual NUMERIC, cp_percentual NUMERIC
            ) AS $$
            DECLARE
                i INT;
            BEGIN
                i := 1;
                WHILE i <= mes LOOP
                    RETURN QUERY
                    SELECT
                        adm_cp.mes AS mes_i,
                        adm_cp.total_salario AS total_salario,
                        adm_cp.total_salario_mk AS total_salario_mk,
                        adm_cp.total_salario_cp AS total_salario_cp,
                        ROUND(adm_cp.total_salario_mk / adm_cp.total_salario * 100, 2) AS mk_percentual,
                        ROUND(adm_cp.total_salario_cp / adm_cp.total_salario * 100, 2) AS cp_percentual

                    FROM
                        (
                            SELECT
                                i AS mes,
                                SUM(salarios.salario) AS total_salario,
                                ROUND(SUM(CASE WHEN salarios.plano_contas = 'MK' THEN salarios.salario WHEN salarios.plano_contas = 'MK/CP' THEN salarios.salario / 2.00 ELSE 0 END), 2) AS total_salario_mk,
                                ROUND(SUM(CASE WHEN salarios.plano_contas = 'CP' THEN salarios.salario WHEN salarios.plano_contas = 'MK/CP' THEN salarios.salario / 2.00 ELSE 0 END), 2) AS total_salario_cp

                            FROM
                                (
                                    SELECT
                                        rh_funcionarios.id,
                                        rh_funcionarios.nome

                                    FROM
                                        rh_funcionarios,
                                        home_jobs

                                    WHERE
                                        rh_funcionarios.job_id = home_jobs.id AND
                                        home_jobs.descricao = 'COPLAS' AND
                                        EXTRACT(YEAR FROM rh_funcionarios.data_entrada) + EXTRACT(MONTH FROM rh_funcionarios.data_entrada) / 100.00 <= ano + i / 100.00 AND
                                        (
                                            rh_funcionarios.data_saida IS NULL OR
                                            EXTRACT(YEAR FROM rh_funcionarios.data_saida) + EXTRACT(MONTH FROM rh_funcionarios.data_saida) / 100.00 >= ano + i / 100.00
                                        )
                                ) funcionarios,
                                (
                                    SELECT
                                        rh_salarios.funcionario_id,
                                        rh_salarios.data,
                                        CASE WHEN rh_salarios.modalidade = 'HORISTA' THEN rh_salarios.salario * 220 ELSE rh_salarios.salario END AS salario,
                                        rh_setores.plano_contas

                                    FROM
                                        rh_salarios,
                                        rh_setores

                                    WHERE
                                        rh_salarios.setor_id = rh_setores.id AND
                                        (rh_salarios.funcionario_id, rh_salarios.data) IN
                                            (
                                                SELECT
                                                    rh_salarios.funcionario_id,
                                                    MAX(rh_salarios.data)

                                                FROM
                                                    rh_salarios

                                                WHERE
                                                    EXTRACT(YEAR FROM rh_salarios.data) + EXTRACT(MONTH FROM rh_salarios.data) / 100.00 <= ano + i / 100.00

                                                GROUP BY
                                                    rh_salarios.funcionario_id
                                            )
                                ) salarios

                            WHERE
                                funcionarios.id = salarios.funcionario_id
                        ) adm_cp;
                    i := i + 1;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;
            """,
            """
            DROP FUNCTION rateio_salario_adm_cp_ano_mes_a_mes;
            """
        ),
    ]
