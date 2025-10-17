import pandas as pd

# TODO: Documentar


def completar_meses(dataframe: pd.DataFrame, nome_coluna_mes: str, colunas_padrao: list[str]):
    """Enviar dataframe com o conteudo de somente 1 ano"""
    meses = pd.DataFrame({nome_coluna_mes: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]})

    if dataframe.empty:
        for coluna in colunas_padrao:
            meses[coluna] = 0
        return meses

    com_meses = pd.merge(dataframe, meses, how='outer', on=nome_coluna_mes).fillna(0)
    com_meses = com_meses.sort_values(by=nome_coluna_mes)

    return com_meses
