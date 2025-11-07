import pandas as pd


def completar_meses(dataframe: pd.DataFrame, nome_coluna_mes: str, colunas_padrao: list[str]) -> pd.DataFrame:
    """Completa um DataFrame com todos os meses de um ano.

    Parametros:
    -----------
    :dataframe [DataFrame]: com o DataFrame a ser completado. Enviar com conteudo de somente 1 ano.
    :nome_coluna_mes [str]: com o nome da coluna que contem o mes para completar.
    :colunas_padrao [list[str]]: com o nome das colunas que precisam existir caso o DataFrame esteja em branco.

    Retorno:
    --------
    :DataFrame: com o DataFrame original completado com todos os meses."""
    meses = pd.DataFrame({nome_coluna_mes: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]})

    if dataframe.empty:
        for coluna in colunas_padrao:
            meses[coluna] = 0
        return meses

    com_meses = pd.merge(dataframe, meses, how='outer', on=nome_coluna_mes).fillna(0)
    com_meses = com_meses.sort_values(by=nome_coluna_mes)

    return com_meses
