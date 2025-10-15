from typing import Literal
from utils.custom import DefaultDict
from utils.oracle.conectar import executar_oracle
import pandas as pd

# TODO: Documentar


def map_relatorio_financeiro_sql_string_placeholders(fonte: Literal['pagar', 'receber',], **kwargs_formulario):
    """
        SQLs estão em um dict onde a chave é o nome do campo do formulario e o valor é um dict com o placeholder como
        chave e o codigo sql como valor
    """

    valor_debito_negativo = kwargs_formulario.pop('valor_debito_negativo', False)
    negativo = ""
    if fonte == 'pagar' and valor_debito_negativo:
        negativo = " * (-1)"

    map_sql_pagar_base = {
        'valor_efetivo': "COALESCE(SUM(PAGAR.VALORPAGO * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000), 0) {negativo} AS VALOR_EFETIVO".format(negativo=negativo),

        'fonte': """
            COPLAS.FORNECEDORES,
            COPLAS.PAGAR,
            COPLAS.PAGAR_PLANOCONTA,
            COPLAS.PAGAR_CENTRORESULTADO,
            COPLAS.PAGAR_JOB,
            COPLAS.JOBS,
        """,

        'fonte_joins': """
            PAGAR.CODFOR = FORNECEDORES.CODFOR AND
            PAGAR_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
            PAGAR.CHAVE = PAGAR_PLANOCONTA.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_CENTRORESULTADO.CHAVE_PAGAR AND
            PAGAR.CHAVE = PAGAR_JOB.CHAVE_PAGAR AND
            PAGAR_JOB.CHAVE_JOB = JOBS.CODIGO AND
        """,

        "fonte_where": "PAGAR.DATAEMISSAO >= TO_DATE('01/01/2010', 'DD-MM-YYYY') AND"
    }

    map_sql_pagar = {
        'coluna_carteira': {'carteira_campo_alias': "'N/A' AS CARTEIRA,", },
        'carteira_parede_de_concreto': {'sem_filtro': "1 = 0 AND", },
        'carteira_premoldado_poste': {'sem_filtro': "1 = 0 AND", },
        'carteira_infra': {'sem_filtro': "1 = 0 AND", },

        'carteira_cobranca': {'carteira_cobranca_pesquisa': "PAGAR.CARTEIRACOBRANCA = :carteira_cobranca AND", },

        'coluna_condicao': {'condicao_campo_alias': "PAGAR.CONDICAO,",
                            'condicao_campo': "PAGAR.CONDICAO,", },
        'condicao': {'condicao_pesquisa': "PAGAR.CONDICAO = :condicao AND", },

        'status_diferente': {'status_diferente_pesquisa': "PAGAR.STATUS != :status_diferente AND", },

        'coluna_cliente': {'cliente_campo_alias': "'N/A' AS CLIENTE,", },
        'cliente': {'cliente_pesquisa': "'N/A' LIKE UPPER(:cliente) AND", },

        'coluna_fornecedor': {'fornecedor_campo_alias': "FORNECEDORES.NOMERED AS FORNECEDOR,",
                              'fornecedor_campo': "FORNECEDORES.NOMERED,", },
        'fornecedor': {'fornecedor_pesquisa': "UPPER(FORNECEDORES.NOMERED) LIKE UPPER(:fornecedor) AND", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM PAGAR.DATAEMISSAO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM PAGAR.DATAEMISSAO),", },
        'data_emissao_inicio': {'data_emissao_inicio_pesquisa': "PAGAR.DATAEMISSAO >= :data_emissao_inicio AND", },
        'data_emissao_fim': {'data_emissao_fim_pesquisa': "PAGAR.DATAEMISSAO <= :data_emissao_fim AND", },

        'coluna_mes_vencimento': {'mes_vencimento_campo_alias': "EXTRACT(MONTH FROM PAGAR.DATAVENCIMENTO) AS MES_VENCIMENTO,",
                                  'mes_vencimento_campo': "EXTRACT(MONTH FROM PAGAR.DATAVENCIMENTO),", },
        'coluna_data_vencimento': {'data_vencimento_campo_alias': "PAGAR.DATAVENCIMENTO AS DATA_VENCIMENTO,",
                                   'data_vencimento_campo': "PAGAR.DATAVENCIMENTO,", },
        'data_vencimento_inicio': {'data_vencimento_inicio_pesquisa': "PAGAR.DATAVENCIMENTO >= :data_vencimento_inicio AND", },
        'data_vencimento_fim': {'data_vencimento_fim_pesquisa': "PAGAR.DATAVENCIMENTO <= :data_vencimento_fim AND", },

        'coluna_ano_liquidacao': {'ano_liquidacao_campo_alias': "EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO) AS ANO_LIQUIDACAO,",
                                  'ano_liquidacao_campo': "EXTRACT(YEAR FROM PAGAR.DATALIQUIDACAO),", },
        'coluna_mes_liquidacao': {'mes_liquidacao_campo_alias': "EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO) AS MES_LIQUIDACAO,",
                                  'mes_liquidacao_campo': "EXTRACT(MONTH FROM PAGAR.DATALIQUIDACAO),", },
        'coluna_data_liquidacao': {'data_liquidacao_campo_alias': "PAGAR.DATALIQUIDACAO AS DATA_LIQUIDACAO,",
                                   'data_liquidacao_campo': "PAGAR.DATALIQUIDACAO,", },
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa': "PAGAR.DATALIQUIDACAO >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa': "PAGAR.DATALIQUIDACAO <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_campo_alias': "PLANO_DE_CONTAS.CONTA AS CODIGO_PLANO_CONTA,",
                                      'codigo_plano_conta_campo': "PLANO_DE_CONTAS.CONTA,", },
        'coluna_plano_conta': {'plano_conta_campo_alias': "PLANO_DE_CONTAS.DESCRICAO AS PLANO_CONTA,",
                               'plano_conta_campo': "PLANO_DE_CONTAS.DESCRICAO,", },
        'plano_conta': {'plano_conta_pesquisa': "PLANO_DE_CONTAS.CD_PLANOCONTA = :chave_plano_conta AND", },
        'plano_conta_descricao': {'plano_conta_descricao_pesquisa': "(UPPER(PLANO_DE_CONTAS.DESCRICAO) LIKE UPPER(:plano_conta_descricao) OR PLANO_DE_CONTAS.CONTA LIKE :plano_conta_descricao) AND", },
        'plano_conta_frete_cif': {'plano_conta_frete_cif_pesquisa': "PLANO_DE_CONTAS.CD_PLANOCONTA IN (1377, 1580, 1613, 1614, 1616, 1617, 1618) AND", },
        'plano_conta_codigo': {'plano_conta_codigo_pesquisa': "PLANO_DE_CONTAS.CONTA LIKE :plano_conta_codigo AND", },
        'desconsiderar_plano_conta_investimentos': {'desconsiderar_plano_conta_investimentos_pesquisa': "PLANO_DE_CONTAS.CONTA NOT LIKE '4.%' AND", },

        'coluna_valor_titulo': {'valor_titulo_campo_alias': "SUM(PAGAR.VALORTOTAL * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_TITULO,".format(negativo=negativo), },
        'coluna_valor_titulo_liquido_desconto': {'valor_titulo_liquido_desconto_campo_alias': "SUM((PAGAR.VALORTOTAL - PAGAR.ABATIMENTOS_DEVOLUCOES - PAGAR.ABATIMENTOS_OUTROS - COALESCE(PAGAR.DESCONTOS, 0)) * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_LIQUIDO_DESCONTOS,".format(negativo=negativo), },

        'coluna_descontos_totais': {'descontos_totais_campo_alias': ", SUM((PAGAR.ABATIMENTOS_DEVOLUCOES + PAGAR.ABATIMENTOS_OUTROS + COALESCE(PAGAR.DESCONTOS, 0)) * PAGAR_PLANOCONTA.PERCENTUAL * PAGAR_CENTRORESULTADO.PERCENTUAL * PAGAR_JOB.PERCENTUAL / 1000000) {negativo} AS DESCONTOS_TOTAIS".format(negativo=negativo), },

        'coluna_chave_nota': {'chave_nota_campo_alias': "NULL AS CHAVE_NOTA,", },

        'coluna_chave_centro_resultado': {'chave_centro_resultado_campo_alias': "PAGAR_CENTRORESULTADO.CHAVE_CENTRO AS CHAVE_CENTRO_RESULTADO,",
                                          'chave_centro_resultado_campo': "PAGAR_CENTRORESULTADO.CHAVE_CENTRO,", },
        'centro_resultado': {'centro_resultado_pesquisa': "PAGAR_CENTRORESULTADO.CHAVE_CENTRO = :chave_centro_resultado AND", },
        'centro_resultado_coplas': {'centro_resultado_coplas_pesquisa': "PAGAR_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND", },
    }

    map_sql_receber_base = {
        'valor_efetivo': "COALESCE(SUM(RECEBER.VALORRECEBIDO * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000), 0) {negativo} AS VALOR_EFETIVO".format(negativo=negativo),

        'fonte': """
            COPLAS.CLIENTES,
            COPLAS.RECEBER,
            COPLAS.RECEBER_PLANOCONTA,
            COPLAS.RECEBER_CENTRORESULTADO,
            COPLAS.RECEBER_JOB,
            COPLAS.JOBS,
        """,

        'fonte_joins': """
            RECEBER.CODCLI = CLIENTES.CODCLI AND
            RECEBER_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
            RECEBER.CHAVE = RECEBER_PLANOCONTA.CHAVE_RECEBER AND
            RECEBER.CHAVE = RECEBER_CENTRORESULTADO.CHAVE_RECEBER AND
            RECEBER.CHAVE = RECEBER_JOB.CHAVE_RECEBER AND
            RECEBER_JOB.CHAVE_JOB = JOBS.CODIGO AND
        """,

        "fonte_where": "RECEBER.DATAEMISSAO >= TO_DATE('01/01/2010', 'DD-MM-YYYY') AND"
    }

    map_sql_receber = {
        'coluna_carteira': {'carteira_campo_alias': "VENDEDORES.NOMERED AS CARTEIRA,",
                            'carteira_campo': "VENDEDORES.NOMERED,",
                            'carteira_from': "COPLAS.VENDEDORES,",
                            'carteira_join': "CLIENTES.CHAVE_VENDEDOR3 = VENDEDORES.CODVENDEDOR(+) AND", },
        'carteira_parede_de_concreto': {'carteira_parede_de_concreto_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=23) AND", },
        'carteira_premoldado_poste': {'carteira_premoldado_poste_pesquisa': "CLIENTES.CHAVE_TIPO IN (7908, 7904) AND", },
        'carteira_infra': {'carteira_infra_pesquisa': "CLIENTES.CODCLI IN (SELECT DISTINCT CLIENTES_INFORMACOES_CLI.CHAVE_CLIENTE FROM COPLAS.CLIENTES_INFORMACOES_CLI WHERE CLIENTES_INFORMACOES_CLI.CHAVE_INFORMACAO=8) AND", },

        'carteira_cobranca': {'carteira_cobranca_pesquisa': "RECEBER.CARTEIRACOBRANCA = :carteira_cobranca AND", },

        'coluna_condicao': {'condicao_campo_alias': "RECEBER.CONDICAO,",
                            'condicao_campo': "RECEBER.CONDICAO,", },
        'condicao': {'condicao_pesquisa': "RECEBER.CONDICAO = :condicao AND", },

        'status_diferente': {'status_diferente_pesquisa': "RECEBER.STATUS != :status_diferente AND", },

        'coluna_cliente': {'cliente_campo_alias': "CLIENTES.NOMERED AS CLIENTE,",
                           'cliente_campo': "CLIENTES.NOMERED,", },
        'cliente': {'cliente_pesquisa': "UPPER(CLIENTES.NOMERED) LIKE UPPER(:cliente) AND", },

        'coluna_fornecedor': {'fornecedor_campo_alias': "'N/A' AS FORNECEDOR,", },
        'fornecedor': {'fornecedor_pesquisa': "'N/A' LIKE UPPER(:fornecedor) AND", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias': "EXTRACT(MONTH FROM RECEBER.DATAEMISSAO) AS MES_EMISSAO,",
                               'mes_emissao_campo': "EXTRACT(MONTH FROM RECEBER.DATAEMISSAO),", },
        'data_emissao_inicio': {'data_emissao_inicio_pesquisa': "RECEBER.DATAEMISSAO >= :data_emissao_inicio AND", },
        'data_emissao_fim': {'data_emissao_fim_pesquisa': "RECEBER.DATAEMISSAO <= :data_emissao_fim AND", },

        'coluna_mes_vencimento': {'mes_vencimento_campo_alias': "EXTRACT(MONTH FROM RECEBER.DATAVENCIMENTO) AS MES_VENCIMENTO,",
                                  'mes_vencimento_campo': "EXTRACT(MONTH FROM RECEBER.DATAVENCIMENTO),", },
        'coluna_data_vencimento': {'data_vencimento_campo_alias': "RECEBER.DATAVENCIMENTO AS DATA_VENCIMENTO,",
                                   'data_vencimento_campo': "RECEBER.DATAVENCIMENTO,", },
        'data_vencimento_inicio': {'data_vencimento_inicio_pesquisa': "RECEBER.DATAVENCIMENTO >= :data_vencimento_inicio AND", },
        'data_vencimento_fim': {'data_vencimento_fim_pesquisa': "RECEBER.DATAVENCIMENTO <= :data_vencimento_fim AND", },

        'coluna_ano_liquidacao': {'ano_liquidacao_campo_alias': "EXTRACT(YEAR FROM RECEBER.DATALIQUIDACAO) AS ANO_LIQUIDACAO,",
                                  'ano_liquidacao_campo': "EXTRACT(YEAR FROM RECEBER.DATALIQUIDACAO),", },
        'coluna_mes_liquidacao': {'mes_liquidacao_campo_alias': "EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO) AS MES_LIQUIDACAO,",
                                  'mes_liquidacao_campo': "EXTRACT(MONTH FROM RECEBER.DATALIQUIDACAO),", },
        'coluna_data_liquidacao': {'data_liquidacao_campo_alias': "RECEBER.DATALIQUIDACAO AS DATA_LIQUIDACAO,",
                                   'data_liquidacao_campo': "RECEBER.DATALIQUIDACAO,", },
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa': "RECEBER.DATALIQUIDACAO >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa': "RECEBER.DATALIQUIDACAO <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_campo_alias': "PLANO_DE_CONTAS.CONTA AS CODIGO_PLANO_CONTA,",
                                      'codigo_plano_conta_campo': "PLANO_DE_CONTAS.CONTA,", },
        'coluna_plano_conta': {'plano_conta_campo_alias': "PLANO_DE_CONTAS.DESCRICAO AS PLANO_CONTA,",
                               'plano_conta_campo': "PLANO_DE_CONTAS.DESCRICAO,", },
        'plano_conta': {'plano_conta_pesquisa': "PLANO_DE_CONTAS.CD_PLANOCONTA = :chave_plano_conta AND", },
        'plano_conta_descricao': {'plano_conta_descricao_pesquisa': "(UPPER(PLANO_DE_CONTAS.DESCRICAO) LIKE UPPER(:plano_conta_descricao) OR PLANO_DE_CONTAS.CONTA LIKE :plano_conta_descricao) AND", },
        'plano_conta_frete_cif': {'plano_conta_frete_cif_pesquisa': "PLANO_DE_CONTAS.CD_PLANOCONTA IN (1377, 1580, 1613, 1614, 1616, 1617, 1618) AND", },
        'plano_conta_codigo': {'plano_conta_codigo_pesquisa': "PLANO_DE_CONTAS.CONTA LIKE :plano_conta_codigo AND", },
        'desconsiderar_plano_conta_investimentos': {'desconsiderar_plano_conta_investimentos_pesquisa': "PLANO_DE_CONTAS.CONTA NOT LIKE '4.%' AND", },

        'coluna_valor_titulo': {'valor_titulo_campo_alias': "SUM(RECEBER.VALORTOTAL * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_TITULO,".format(negativo=negativo), },
        'coluna_valor_titulo_liquido_desconto': {'valor_titulo_liquido_desconto_campo_alias': "SUM((RECEBER.VALORTOTAL - RECEBER.ABATIMENTOS_DEVOLUCOES - RECEBER.ABATIMENTOS_OUTROS - COALESCE(RECEBER.DESCONTOS, 0)) * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_LIQUIDO_DESCONTOS,".format(negativo=negativo), },

        'coluna_descontos_totais': {'descontos_totais_campo_alias': ", SUM((RECEBER.ABATIMENTOS_DEVOLUCOES + RECEBER.ABATIMENTOS_OUTROS + COALESCE(RECEBER.DESCONTOS, 0)) * RECEBER_PLANOCONTA.PERCENTUAL * RECEBER_CENTRORESULTADO.PERCENTUAL * RECEBER_JOB.PERCENTUAL / 1000000) {negativo} AS DESCONTOS_TOTAIS".format(negativo=negativo), },

        'coluna_chave_nota': {'chave_nota_campo_alias': "RECEBER.CHAVE_NOTA,",
                              'chave_nota_campo': "RECEBER.CHAVE_NOTA,", },

        'coluna_chave_centro_resultado': {'chave_centro_resultado_campo_alias': "RECEBER_CENTRORESULTADO.CHAVE_CENTRO AS CHAVE_CENTRO_RESULTADO,",
                                          'chave_centro_resultado_campo': "RECEBER_CENTRORESULTADO.CHAVE_CENTRO,", },
        'centro_resultado': {'centro_resultado_pesquisa': "RECEBER_CENTRORESULTADO.CHAVE_CENTRO = :chave_centro_resultado AND", },
        'centro_resultado_coplas': {'centro_resultado_coplas_pesquisa': "RECEBER_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND", },
    }

    tipo_movimentacao_bancaria = 'C' if fonte == 'receber' else 'D'
    map_sql_movimentacao_bancaria_base = {
        'valor_efetivo_mov_ban': "SUM(MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_EFETIVO".format(negativo=negativo),
        'valor_efetivo_union_alias': "SUM(VALOR_EFETIVO) AS VALOR_EFETIVO",

        'fonte_where_mov_ban': "MOVBAN.TIPO = '{}' AND".format(tipo_movimentacao_bancaria),
    }

    map_sql_movimentacao_bancaria = {
        'coluna_carteira': {'carteira_campo_alias_mov_ban': "'N/A' AS CARTEIRA,",
                            'carteira_union_alias': "CARTEIRA,", },
        'carteira_parede_de_concreto': {'sem_filtro_mov_ban': "1 = 0 AND", },
        'carteira_premoldado_poste': {'sem_filtro_mov_ban': "1 = 0 AND", },
        'carteira_infra': {'sem_filtro_mov_ban': "1 = 0 AND", },

        'carteira_cobranca': {'sem_filtro_mov_ban': "1 = 0 AND", },

        'coluna_condicao': {'condicao_campo_alias_mov_ban': "'LIQUIDADO' AS CONDICAO,",
                            'condicao_union_alias': "CONDICAO,", },
        'condicao': {'condicao_pesquisa_mov_ban': "'LIQUIDADO' = :condicao AND", },

        'status_diferente': {'status_diferente_pesquisa_mov_ban': "MOVBAN.STATUS != :status_diferente AND", },

        'coluna_cliente': {'cliente_campo_alias_mov_ban': "'N/A' AS CLIENTE,",
                           'cliente_union_alias': "CLIENTE,", },
        'cliente': {'sem_filtro_mov_ban': "1 = 0 AND", },

        'coluna_fornecedor': {'fornecedor_campo_alias_mov_ban': "'N/A' AS FORNECEDOR,",
                              'fornecedor_union_alias': "FORNECEDOR,", },
        'fornecedor': {'sem_filtro_mov_ban': "1 = 0 AND", },

        'coluna_job': {'job_union_alias': "JOB,", },

        'coluna_mes_emissao': {'mes_emissao_campo_alias_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA) AS MES_EMISSAO,",
                               'mes_emissao_campo_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA),",
                               'mes_emissao_union_alias': "MES_EMISSAO,", },
        'data_emissao_inicio': {'data_emissao_inicio_pesquisa_mov_ban': "MOVBAN.DATA >= :data_emissao_inicio AND", },
        'data_emissao_fim': {'data_emissao_fim_pesquisa_mov_ban': "MOVBAN.DATA <= :data_emissao_fim AND", },

        'coluna_mes_vencimento': {'mes_vencimento_campo_alias_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA) AS MES_VENCIMENTO,",
                                  'mes_vencimento_campo_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA),",
                                  'mes_vencimento_union_alias': "MES_VENCIMENTO,", },
        'coluna_data_vencimento': {'data_vencimento_campo_alias_mov_ban': "MOVBAN.DATA AS DATA_VENCIMENTO,",
                                   'data_vencimento_campo_mov_ban': "MOVBAN.DATA,",
                                   'data_vencimento_union_alias': "DATA_VENCIMENTO,", },
        'data_vencimento_inicio': {'data_vencimento_inicio_pesquisa_mov_ban': "MOVBAN.DATA >= :data_vencimento_inicio AND", },
        'data_vencimento_fim': {'data_vencimento_fim_pesquisa_mov_ban': "MOVBAN.DATA <= :data_vencimento_fim AND", },

        'coluna_ano_liquidacao': {'ano_liquidacao_campo_alias_mov_ban': "EXTRACT(YEAR FROM MOVBAN.DATA) AS ANO_LIQUIDACAO,",
                                  'ano_liquidacao_campo_mov_ban': "EXTRACT(YEAR FROM MOVBAN.DATA),",
                                  'ano_liquidacao_union_alias': "ANO_LIQUIDACAO,", },
        'coluna_mes_liquidacao': {'mes_liquidacao_campo_alias_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA) AS MES_LIQUIDACAO,",
                                  'mes_liquidacao_campo_mov_ban': "EXTRACT(MONTH FROM MOVBAN.DATA),",
                                  'mes_liquidacao_union_alias': "MES_LIQUIDACAO,", },
        'coluna_data_liquidacao': {'data_liquidacao_campo_alias_mov_ban': "MOVBAN.DATA AS DATA_LIQUIDACAO,",
                                   'data_liquidacao_campo_mov_ban': "MOVBAN.DATA,",
                                   'data_liquidacao_union_alias': "DATA_LIQUIDACAO,", },
        'data_liquidacao_inicio': {'data_liquidacao_inicio_pesquisa_mov_ban': "MOVBAN.DATA >= :data_liquidacao_inicio AND", },
        'data_liquidacao_fim': {'data_liquidacao_fim_pesquisa_mov_ban': "MOVBAN.DATA <= :data_liquidacao_fim AND", },

        'coluna_codigo_plano_conta': {'codigo_plano_conta_union_alias': "CODIGO_PLANO_CONTA,", },
        'coluna_plano_conta': {'plano_conta_union_alias': "PLANO_CONTA,", },

        'coluna_valor_titulo': {'valor_titulo_campo_alias_mov_ban': "SUM(MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_TITULO,".format(negativo=negativo),
                                'valor_titulo_union_alias': "SUM(VALOR_TITULO) AS VALOR_TITULO,", },
        'coluna_valor_titulo_liquido_desconto': {'valor_titulo_liquido_desconto_campo_alias_mov_ban': "SUM(MOVBAN.VALOR * MOVBAN_PLANOCONTA.PERCENTUAL * MOVBAN_CENTRORESULTADO.PERCENTUAL * MOVBAN_JOB.PERCENTUAL / 1000000) {negativo} AS VALOR_LIQUIDO_DESCONTOS,".format(negativo=negativo),
                                                 'valor_titulo_liquido_desconto_union_alias': "SUM(VALOR_LIQUIDO_DESCONTOS) AS VALOR_LIQUIDO_DESCONTOS,", },

        'coluna_descontos_totais': {'descontos_totais_campo_alias_mov_ban': ", 0 AS DESCONTOS_TOTAIS",
                                    'descontos_totais_union_alias': ", SUM(DESCONTOS_TOTAIS) AS DESCONTOS_TOTAIS", },

        'coluna_chave_nota': {'chave_nota_campo_alias_mov_ban': "NULL AS CHAVE_NOTA,",
                              'chave_nota_union_alias': "CHAVE_NOTA,", },

        'coluna_chave_centro_resultado': {'chave_centro_resultado_campo_alias_mov_ban': "MOVBAN_CENTRORESULTADO.CHAVE_CENTRO AS CHAVE_CENTRO_RESULTADO,",
                                          'chave_centro_resultado_campo_mov_ban': "MOVBAN_CENTRORESULTADO.CHAVE_CENTRO,",
                                          'chave_centro_resultado_union_alias': "CHAVE_CENTRO_RESULTADO,", },
        'centro_resultado': {'centro_resultado_pesquisa_mov_ban': "MOVBAN_CENTRORESULTADO.CHAVE_CENTRO = :chave_centro_resultado AND", },
        'centro_resultado_coplas': {'centro_resultado_coplas_pesquisa_mov_ban': "MOVBAN_CENTRORESULTADO.CHAVE_CENTRO IN (38, 44, 45, 47) AND", },
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

    codigo_sql = kwargs.get('codigo_sql')
    data_liquidacao_inicio = kwargs.get('data_liquidacao_inicio')
    data_liquidacao_fim = kwargs.get('data_liquidacao_fim')
    data_vencimento_inicio = kwargs.get('data_vencimento_inicio')
    data_vencimento_fim = kwargs.get('data_vencimento_fim')
    plano_conta = kwargs.get('plano_conta')
    job = kwargs.get('job')
    plano_conta_codigo = kwargs.get('plano_conta_codigo')
    plano_conta_descricao = kwargs.get('plano_conta_descricao')
    fornecedor = kwargs.get('fornecedor')
    data_emissao_inicio = kwargs.get('data_emissao_inicio')
    data_emissao_fim = kwargs.get('data_emissao_fim')
    status_diferente = kwargs.get('status_diferente')
    centro_resultado = kwargs.get('centro_resultado')
    condicao = kwargs.get('condicao')
    carteira_cobranca = kwargs.get('carteira_cobranca')
    cliente = kwargs.get('cliente')

    kwargs_sql.update(map_relatorio_financeiro_sql_string_placeholders(fonte, **kwargs))

    # kwargs_ora precisa conter os placeholders corretamente

    if codigo_sql:
        kwargs_ora.update({'codigo_sql': codigo_sql, })

    if data_liquidacao_inicio:
        kwargs_ora.update({'data_liquidacao_inicio': data_liquidacao_inicio})

    if data_liquidacao_fim:
        kwargs_ora.update({'data_liquidacao_fim': data_liquidacao_fim})

    if data_vencimento_inicio:
        kwargs_ora.update({'data_vencimento_inicio': data_vencimento_inicio})

    if data_vencimento_fim:
        kwargs_ora.update({'data_vencimento_fim': data_vencimento_fim})

    if plano_conta:
        chave_plano_conta = plano_conta if isinstance(plano_conta, int) else plano_conta.pk
        kwargs_ora.update({'chave_plano_conta': chave_plano_conta, })

    if job:
        chave_job = job if isinstance(job, int) else job.pk
        kwargs_ora.update({'chave_job': chave_job, })

    if plano_conta_codigo:
        kwargs_ora.update({'plano_conta_codigo': plano_conta_codigo})

    if plano_conta_descricao:
        kwargs_ora.update({'plano_conta_descricao': plano_conta_descricao})

    if fornecedor:
        kwargs_ora.update({'fornecedor': fornecedor})

    if data_emissao_inicio:
        kwargs_ora.update({'data_emissao_inicio': data_emissao_inicio})

    if data_emissao_fim:
        kwargs_ora.update({'data_emissao_fim': data_emissao_fim})

    if status_diferente:
        kwargs_ora.update({'status_diferente': status_diferente})

    if centro_resultado:
        chave_centro_resultado = centro_resultado if isinstance(centro_resultado, int) else centro_resultado.pk
        kwargs_ora.update({'chave_centro_resultado': chave_centro_resultado, })

    if condicao:
        kwargs_ora.update({'condicao': condicao})

    if carteira_cobranca:
        kwargs_ora.update({'carteira_cobranca': carteira_cobranca})

    if cliente:
        kwargs_ora.update({'cliente': cliente})

    sql_base = """
        SELECT
            {job_union_alias}
            {mes_emissao_union_alias}
            {mes_vencimento_union_alias}
            {ano_liquidacao_union_alias}
            {mes_liquidacao_union_alias}
            {chave_centro_resultado_union_alias}
            {codigo_plano_conta_union_alias}
            {plano_conta_union_alias}
            {chave_nota_union_alias}
            {data_vencimento_union_alias}
            {data_liquidacao_union_alias}
            {fornecedor_union_alias}
            {carteira_union_alias}
            {cliente_union_alias}
            {condicao_union_alias}
            {valor_titulo_union_alias}
            {valor_titulo_liquido_desconto_union_alias}

            {valor_efetivo_union_alias}

            {descontos_totais_union_alias}

        FROM
            (
                SELECT
                    {job_campo_alias}
                    {mes_emissao_campo_alias}
                    {mes_vencimento_campo_alias}
                    {ano_liquidacao_campo_alias}
                    {mes_liquidacao_campo_alias}
                    {chave_centro_resultado_campo_alias}
                    {codigo_plano_conta_campo_alias}
                    {plano_conta_campo_alias}
                    {chave_nota_campo_alias}
                    {data_vencimento_campo_alias}
                    {data_liquidacao_campo_alias}
                    {fornecedor_campo_alias}
                    {carteira_campo_alias}
                    {cliente_campo_alias}
                    {condicao_campo_alias}
                    {valor_titulo_campo_alias}
                    {valor_titulo_liquido_desconto_campo_alias}

                    {valor_efetivo}

                    {descontos_totais_campo_alias}

                FROM
                    {fonte}
                    {carteira_from}
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    {sem_filtro}
                    {fonte_joins}
                    {carteira_join}
                    PLANO_DE_CONTAS.CD_PLANOCONTA != 1551 AND
                    {fonte_where}

                    {data_liquidacao_inicio_pesquisa}
                    {data_liquidacao_fim_pesquisa}
                    {data_vencimento_inicio_pesquisa}
                    {data_vencimento_fim_pesquisa}
                    {plano_conta_pesquisa}
                    {job_pesquisa}
                    {plano_conta_codigo_pesquisa}
                    {centro_resultado_coplas_pesquisa}
                    {fornecedor_pesquisa}
                    {data_emissao_inicio_pesquisa}
                    {data_emissao_fim_pesquisa}
                    {status_diferente_pesquisa}
                    {plano_conta_frete_cif_pesquisa}
                    {centro_resultado_pesquisa}
                    {condicao_pesquisa}
                    {carteira_cobranca_pesquisa}
                    {cliente_pesquisa}
                    {plano_conta_descricao_pesquisa}
                    {desconsiderar_plano_conta_investimentos_pesquisa}
                    {carteira_parede_de_concreto_pesquisa}
                    {carteira_premoldado_poste_pesquisa}
                    {carteira_infra_pesquisa}

                    1 = 1

                GROUP BY
                    {mes_emissao_campo}
                    {mes_liquidacao_campo}
                    {codigo_plano_conta_campo}
                    {chave_nota_campo}
                    {data_vencimento_campo}
                    {fornecedor_campo}
                    {mes_vencimento_campo}
                    {ano_liquidacao_campo}
                    {cliente_campo}
                    {chave_centro_resultado_campo}
                    {plano_conta_campo}
                    {data_liquidacao_campo}
                    {job_campo}
                    {condicao_campo}
                    {carteira_campo}
                    1

                UNION ALL

                SELECT
                    {job_campo_alias}
                    {mes_emissao_campo_alias_mov_ban}
                    {mes_vencimento_campo_alias_mov_ban}
                    {ano_liquidacao_campo_alias_mov_ban}
                    {mes_liquidacao_campo_alias_mov_ban}
                    {chave_centro_resultado_campo_alias_mov_ban}
                    {codigo_plano_conta_campo_alias}
                    {plano_conta_campo_alias}
                    {chave_nota_campo_alias_mov_ban}
                    {data_vencimento_campo_alias_mov_ban}
                    {data_liquidacao_campo_alias_mov_ban}
                    {fornecedor_campo_alias_mov_ban}
                    {carteira_campo_alias_mov_ban}
                    {cliente_campo_alias_mov_ban}
                    {condicao_campo_alias_mov_ban}
                    {valor_titulo_campo_alias_mov_ban}
                    {valor_titulo_liquido_desconto_campo_alias_mov_ban}

                    {valor_efetivo_mov_ban}

                    {descontos_totais_campo_alias_mov_ban}

                FROM
                    COPLAS.MOVBAN,
                    COPLAS.MOVBAN_PLANOCONTA,
                    COPLAS.MOVBAN_CENTRORESULTADO,
                    COPLAS.MOVBAN_JOB,
                    COPLAS.JOBS,
                    COPLAS.PLANO_DE_CONTAS

                WHERE
                    {sem_filtro_mov_ban}
                    MOVBAN_PLANOCONTA.CHAVE_PLANOCONTAS = PLANO_DE_CONTAS.CD_PLANOCONTA AND
                    MOVBAN.CHAVE = MOVBAN_PLANOCONTA.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_CENTRORESULTADO.CHAVE_MOVBAN AND
                    MOVBAN.CHAVE = MOVBAN_JOB.CHAVE_MOVBAN AND
                    MOVBAN_JOB.CHAVE_JOB = JOBS.CODIGO AND
                    MOVBAN.AUTOMATICO = 'NAO' AND
                    MOVBAN.DATA >= TO_DATE('01/01/2010', 'DD-MM-YYYY') AND
                    PLANO_DE_CONTAS.CD_PLANOCONTA != 1551 AND
                    {fonte_where_mov_ban}

                    {data_liquidacao_inicio_pesquisa_mov_ban}
                    {data_liquidacao_fim_pesquisa_mov_ban}
                    {data_vencimento_inicio_pesquisa_mov_ban}
                    {data_vencimento_fim_pesquisa_mov_ban}
                    {plano_conta_pesquisa}
                    {job_pesquisa}
                    {plano_conta_codigo_pesquisa}
                    {centro_resultado_coplas_pesquisa_mov_ban}
                    {data_emissao_inicio_pesquisa_mov_ban}
                    {data_emissao_fim_pesquisa_mov_ban}
                    {status_diferente_pesquisa_mov_ban}
                    {plano_conta_frete_cif_pesquisa}
                    {centro_resultado_pesquisa_mov_ban}
                    {condicao_pesquisa_mov_ban}
                    {plano_conta_descricao_pesquisa}
                    {desconsiderar_plano_conta_investimentos_pesquisa}

                    1 = 1

                GROUP BY
                    {mes_emissao_campo_mov_ban}
                    {mes_liquidacao_campo_mov_ban}
                    {codigo_plano_conta_campo}
                    {data_vencimento_campo_mov_ban}
                    {mes_vencimento_campo_mov_ban}
                    {ano_liquidacao_campo_mov_ban}
                    {chave_centro_resultado_campo_mov_ban}
                    {plano_conta_campo}
                    {data_liquidacao_campo_mov_ban}
                    {job_campo}
                    1
            )

        GROUP BY
            {mes_emissao_union_alias}
            {codigo_plano_conta_union_alias}
            {chave_nota_union_alias}
            {data_vencimento_union_alias}
            {mes_liquidacao_union_alias}
            {fornecedor_union_alias}
            {mes_vencimento_union_alias}
            {ano_liquidacao_union_alias}
            {cliente_union_alias}
            {chave_centro_resultado_union_alias}
            {plano_conta_union_alias}
            {data_liquidacao_union_alias}
            {job_union_alias}
            {condicao_union_alias}
            {carteira_union_alias}
            1

        ORDER BY
            {job_union_alias}
            {mes_emissao_union_alias}
            {mes_vencimento_union_alias}
            {ano_liquidacao_union_alias}
            {mes_liquidacao_union_alias}
            {chave_centro_resultado_union_alias}
            {codigo_plano_conta_union_alias}
            {plano_conta_union_alias}
            {data_vencimento_union_alias}
            {data_liquidacao_union_alias}
            {fornecedor_union_alias}
            {carteira_union_alias}
            {cliente_union_alias}
            {condicao_union_alias}
            VALOR_EFETIVO DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, **kwargs_ora)

    return resultado


def get_relatorios_financeiros_faturamentos(relatorio_vendas_faturamento: pd.DataFrame,
                                            relatorio_financeiro_receber: pd.DataFrame, *,
                                            coluna_valor_titulo_mercadorias_liquido_descontos=False,
                                            coluna_valor_efetivo_titulo_mercadorias=False):
    """Relatorio faturamento precisa ter a coluna CHAVE_DOCUMENTO e relatorio receber precisa ter a coluna CHAVE_NOTA"""
    resultado = pd.merge(relatorio_vendas_faturamento, relatorio_financeiro_receber, how='inner',
                         left_on='CHAVE_DOCUMENTO', right_on='CHAVE_NOTA')

    if coluna_valor_titulo_mercadorias_liquido_descontos:
        resultado['VALOR_LIQUIDO_DESCONTOS_MERCADORIAS'] = resultado['VALOR_LIQUIDO_DESCONTOS'] * \
            resultado['PROPORCAO_MERCADORIAS']

    if coluna_valor_efetivo_titulo_mercadorias:
        resultado['VALOR_EFETIVO_MERCADORIAS'] = resultado['VALOR_EFETIVO'] * resultado['PROPORCAO_MERCADORIAS']

    return resultado
