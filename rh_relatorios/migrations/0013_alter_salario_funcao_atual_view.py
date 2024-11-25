# Criado manualmente

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rh_relatorios', '0012_alter_salario_funcao_atual_view'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE OR REPLACE VIEW rh_salario_funcao_atual_view AS
                SELECT
                    rh_salarios.funcionario_id,
                    rh_funcionarios.data_entrada,
                    rh_salarios.data,
                    rh_setores.descricao AS setor,
                    rh_funcoes.descricao AS funcao,
                    rh_salarios.motivo,
                    rh_salarios.modalidade,
                    rh_salarios.salario,
                    CASE WHEN rh_salarios.modalidade = 'HORISTA' THEN rh_salarios.salario * 220 ELSE rh_salarios.salario END AS salario_convertido,
                    rh_salarios.comissao_carteira,
                    rh_salarios.comissao_dupla,
                    rh_salarios.comissao_geral,
                    rh_salarios.observacoes,
                    ROW_NUMBER() OVER() AS id,
                    home_jobs.descricao AS job,
                    rh_funcionarios.nome

                FROM
                    rh_salarios,
                    rh_funcoes,
                    rh_setores,
                    rh_funcionarios,
                    home_jobs

                WHERE
                    rh_funcionarios.job_id = home_jobs.id AND
                    rh_salarios.funcionario_id = rh_funcionarios.id AND
                    rh_salarios.funcao_id = rh_funcoes.id AND
                    rh_salarios.setor_id = rh_setores.id AND
                    (rh_salarios.funcionario_id, rh_salarios.data) IN (SELECT rh_salarios.funcionario_id, MAX(rh_salarios.data) FROM rh_salarios GROUP BY rh_salarios.funcionario_id) AND
                    rh_funcionarios.data_saida IS NULL;
            """
        ),
    ]
