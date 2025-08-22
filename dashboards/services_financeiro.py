from typing import Literal
from utils.custom import DefaultDict
from utils.oracle.conectar import executar_oracle


def map_relatorio_financeiro_sql_string_placeholders(fonte: Literal['pagar', 'receber',], **kwargs_formulario):
    """
        SQLs estão em um dict onde a chave é o nome do campo do formulario e o valor é um dict com o placeholder como
        chave e o codigo sql como valor
    """
    map_sql_pagar_base = {
        'valor_efetivo': "SUM(PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000) AS VALOR_EFETIVO",

        'fonte': """
            COPLAS.PAGAR,
            COPLAS.PAGAR_PLANOCONTA,
            COPLAS.PAGAR_CENTRORESULTADO,
            COPLAS.PAGAR_JOB,
        """,

        'fonte_joins': """
            PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
            PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
        """,
    }

    map_sql_pagar = {
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa': "PAGAR.DATALIQUIDACAO >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa': "PAGAR.DATALIQUIDACAO <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_campo_alias': "PLANO_DE_CONTAS.CONTA AS CODIGO_PLANO_CONTA,",
                                      'codigo_plano_conta_campo': "PLANO_DE_CONTAS.CONTA,", },
    }

    map_sql_receber_base = {
        'valor_efetivo': "SUM(RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000) AS VALOR_EFETIVO",

        'fonte': """
            COPLAS.RECEBER,
            COPLAS.RECEBER_PLANOCONTA,
            COPLAS.RECEBER_CENTRORESULTADO,
            COPLAS.RECEBER_JOB,
        """,

        'fonte_joins': """
            RECEBER_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
            RECEBER.CHAVE = RECEBER_PLANOCONTA.CHAVE_RECEBER AND
            RECEBER.CHAVE = RECEBER_CENTRORESULTADO.CHAVE_RECEBER AND
            RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND
        """,
    }

    map_sql_receber = {
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa': "RECEBER.DATALIQUIDACAO >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa': "RECEBER.DATALIQUIDACAO <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_campo_alias': "PLANO_DE_CONTAS.CONTA AS CODIGO_PLANO_CONTA,",
                                      'codigo_plano_conta_campo': "PLANO_DE_CONTAS.CONTA,", },
    }

    tipo_movimentacao_bancaria = 'C' if fonte == 'receber' else 'D'
    map_sql_movimentacao_bancaria_base = {
        'valor_efetivo_mov_ban': "SUM(MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) AS VALOR_EFETIVO",
        'valor_efetivo_union_alias': "SUM(VALOR_EFETIVO) AS VALOR_EFETIVO",

        'fonte_where_mov_ban': "MOVBAN.TIPO = '{}' AND".format(tipo_movimentacao_bancaria),
    }

    map_sql_movimentacao_bancaria = {
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa_mov_ban': "MOVBAN.DATA >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa_mov_ban': "MOVBAN.DATA <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_union_alias': "CODIGO_PLANO_CONTA,", },
    }

    sql_final = {}
    if fonte == 'receber':
        sql_final.update(map_sql_receber_base)
    else:
        sql_final.update(map_sql_pagar_base)
    sql_final.update(map_sql_movimentacao_bancaria_base)

    for chave, valor in kwargs_formulario.items():
        if valor:
            if fonte == 'receber':
                get_map_receber = map_sql_receber.get(chave)
                if get_map_receber:
                    sql_final.update(get_map_receber)  # type:ignore
            else:
                get_map_pagar = map_sql_pagar.get(chave)
                if get_map_pagar:
                    sql_final.update(get_map_pagar)  # type:ignore

            get_map_movimentacao_bancaria = map_sql_movimentacao_bancaria.get(chave)
            if get_map_movimentacao_bancaria:
                sql_final.update(get_map_movimentacao_bancaria)  # type:ignore

    return sql_final


def get_relatorios_financeiros(fonte: Literal['pagar', 'receber',], **kwargs):
    kwargs_sql = {}
    kwargs_ora = {}

    data_liquidacao_inicio = kwargs.get('data_liquidacao_inicio')
    data_liquidacao_fim = kwargs.get('data_liquidacao_fim')

    kwargs_sql.update(map_relatorio_financeiro_sql_string_placeholders(fonte, **kwargs))

    # kwargs_ora precisa conter os placeholders corretamente

    if data_liquidacao_inicio:
        kwargs_ora.update({'data_liquidacao_inicio': data_liquidacao_inicio})

    if data_liquidacao_fim:
        kwargs_ora.update({'data_liquidacao_fim': data_liquidacao_fim})

    sql_base = """
        SELECT
            {codigo_plano_conta_union_alias}

            {valor_efetivo_union_alias}

        FROM
            (
                SELECT
                    {codigo_plano_conta_campo_alias}

                    {valor_efetivo}

                FROM
                    {fonte}
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    {fonte_joins}

                    {data_liquidacao_inicio_pesquisa}
                    {data_liquidacao_fim_pesquisa}

                    1 = 1

                GROUP BY
                    {codigo_plano_conta_campo}
                    1

                UNION ALL

                SELECT
                    {codigo_plano_conta_campo_alias}

                    {valor_efetivo_mov_ban}

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN.AUTOMATICO = 'NAO' AND
                    {fonte_where_mov_ban}

                    {data_liquidacao_inicio_pesquisa_mov_ban}
                    {data_liquidacao_fim_pesquisa_mov_ban}

                    1 = 1

                GROUP BY
                    {codigo_plano_conta_campo}
                    1
            )

        GROUP BY
            {codigo_plano_conta_union_alias}
            1

        ORDER BY
            {codigo_plano_conta_union_alias}
            VALOR_EFETIVO DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, **kwargs_ora)

    return resultado
