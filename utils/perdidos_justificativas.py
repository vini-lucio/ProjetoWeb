def justificativas(excluidos: bool, considerar_invalidas: bool = False):
    """Retorna filtros SQL de justificativas em itens de orçamentos que não são realmente perdidos (invalidas),
    ex: erros de medida, troca de CNPJ, troca de modelo, etc.

    Parametros:
    -----------
    :excluidos [bool]: boolano se será justificativas da tabela de itens de orçamentos excluidos ou a tabela normal de itens de orçamentos.
    :considerar_invalidas [bool, Dafault False]: boolano se o filtro é para considerar ou desconsiderar as justificativas invalidas.

    Retorno:
    --------
    :str: com o codigo SQL com os filtros."""
    tabela_campo_status = "ORCAMENTOS_ITENS.STATUS"
    tabela_campo_justificativa = "ORCAMENTOS_ITENS.PERDA_JUSTIFICATIVA"
    if excluidos:
        tabela_campo_status = "ORCAMENTOS_ITENS_EXCLUIDOS.STATUS"
        tabela_campo_justificativa = "ORCAMENTOS_ITENS_EXCLUIDOS.JUSTIFICATIVA_PERDA"

    not_like = "NOT"
    if considerar_invalidas:
        not_like = ""

    justificativas = """
        (
            {tabela_campo_status} NOT IN ('CANCELADO', 'PERDA P/ OUTROS') OR
            (
                {tabela_campo_status} IN ('CANCELADO', 'PERDA P/ OUTROS') AND
                {tabela_campo_justificativa} LIKE '____%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%ABRIU OUTRO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%ALTE_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%AMOSTRA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%DUAS V%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%DUPLI%' AND
                {tabela_campo_justificativa} {not_like} LIKE 'ERRAD_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '% ERRAD_' AND
                {tabela_campo_justificativa} {not_like} LIKE '% ERRAD_%' AND
                {tabela_campo_justificativa} {not_like} LIKE 'ERRO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '% ERRO' AND
                {tabela_campo_justificativa} {not_like} LIKE '% ERRO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRA%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCA%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDEI%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%CNPJ%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%QUANTIDADE%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%MATERIAL%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%CPF%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%PRODUTO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%ITE_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%MUDOU%MODELO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%CNPJ%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%QUANTIDADE%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%MATERIAL%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%CPF%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%PRODUTO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%ITE_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%MODELO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%OR_AMENTO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%PEDIDO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%OUTRO%CADASTRO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%REPLI%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%SEPARA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%SUBS%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TESTE%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCA%ITE_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCA%MATERIA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCA%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%CNPJ%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%QUANTIDADE%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%MATERIAL%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%CPF%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%PRODUTO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%MEDIDA%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%ITE_%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROCO%MODELO%' AND
                {tabela_campo_justificativa} {not_like} LIKE '%TROQU%'
            )
        )
    """

    justificativas = justificativas.format(tabela_campo_status=tabela_campo_status,
                                           tabela_campo_justificativa=tabela_campo_justificativa, not_like=not_like)

    return justificativas
