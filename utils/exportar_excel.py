import openpyxl


def arquivo_excel(conteudo: list[list], cabecalho: list = []):
    """Gera arquivo excel sem salvar"""
    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    if worksheet:
        if cabecalho:
            worksheet.append(cabecalho)

        for linha in conteudo:
            worksheet.append(linha)

    return workbook
