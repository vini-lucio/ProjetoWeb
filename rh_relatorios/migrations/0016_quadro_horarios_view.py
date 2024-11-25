# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0015_funcionarioshistoricosalarios'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE VIEW rh_quadro_horarios_view AS
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    rh_salario_funcao_atual_view.job,
                    rh_funcionarios.registro,
                    rh_funcionarios.nome,
                    rh_funcionarios.carteira_profissional,
                    rh_salario_funcao_atual_view.setor,
                    rh_salario_funcao_atual_view.funcao,
                    TO_CHAR(horarios.inicio, 'HH24:MI') || ' - ' || TO_CHAR(horarios.fim, 'HH24:MI') AS horario,
                    TO_CHAR(horarios.intervalo_inicio, 'HH24:MI') || ' - ' || TO_CHAR(horarios.intervalo_fim, 'HH24:MI') AS almoco

                FROM
                    (
                        SELECT
                            rh_horariosfuncionarios.funcionario_id,
                            rh_horarios.inicio,
                            rh_horarios.fim,
                            rh_horarios.intervalo_inicio,
                            rh_horarios.intervalo_fim

                        FROM
                            rh_horarios,
                            rh_horariosfuncionarios

                        WHERE
                            rh_horariosfuncionarios.horario_id = rh_horarios.id AND
                            rh_horariosfuncionarios.data_fim IS NULL
                    ) horarios,
                    rh_salario_funcao_atual_view,
                    rh_funcionarios

                WHERE
                    horarios.funcionario_id = rh_funcionarios.id AND
                    rh_funcionarios.id = rh_salario_funcao_atual_view.funcionario_id;
            """,
            """
            DROP VIEW rh_quadro_horarios_view;
            """
        ),
    ]
