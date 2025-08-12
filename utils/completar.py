import pandas as pd


def completar_meses(dataframe: pd.DataFrame, to_dict: bool = False):
    """Enviar dataframe com o conteudo de somente 1 ano e a coluna do mes com nome MES_EMISSAO"""
    meses = pd.DataFrame({'MES_EMISSAO': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]})

    com_meses = pd.merge(dataframe, meses, how='outer', on='MES_EMISSAO').fillna(0)
    com_meses = com_meses.sort_values(by='MES_EMISSAO')

    if to_dict:
        com_meses = com_meses.to_dict(orient='records')

    return com_meses
