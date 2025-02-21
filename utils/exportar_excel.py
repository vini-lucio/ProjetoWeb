import openpyxl
from io import BytesIO


def arquivo_excel(conteudo: list[list] | list[dict], cabecalho: list = [], titulo: str = '', nova_aba: openpyxl.Workbook | None = None):
    """Gera arquivo excel sem salvar. Quando o conteudo for uma lista de dicionarios o cabeçalho sempre será as chaves do primeiro item do dicionario.
    Passar workbook em noba_aba para adicionar nova aba apos executar uma vez sem"""
    if not nova_aba:
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
    else:
        workbook = nova_aba
        worksheet = workbook.create_sheet()

    if worksheet:
        if titulo:
            worksheet.title = titulo

        if conteudo:
            if isinstance(conteudo[0], dict):
                cabecalho = list(conteudo[0].keys())
                conteudo = [[linha.get(chave) for chave in cabecalho] for linha in conteudo]  # type:ignore

        if cabecalho:
            worksheet.append(cabecalho)

        for linha in conteudo:
            worksheet.append(linha)

    return workbook


def salvar_excel_temporario(workbook: openpyxl.Workbook) -> BytesIO:
    """Retorna o byte stream na posição inicial com o objeto salvo"""
    byte_stream = BytesIO()
    workbook.save(byte_stream)
    byte_stream.seek(0)
    return byte_stream
