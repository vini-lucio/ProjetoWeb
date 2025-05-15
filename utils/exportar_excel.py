from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, PatternFill
from io import BytesIO


def arquivo_excel(conteudo: list[list] | list[dict], cabecalho: list = [], titulo: str = '',
                  nova_aba: openpyxl.Workbook | None = None, cabecalho_negrito: bool = False,
                  formatar_numero: tuple[list[str], int] | None = None,
                  formatar_data: list[str] | None = None,
                  ajustar_largura_colunas: bool = False):
    """Gera arquivo excel sem salvar. Quando o conteudo for uma lista de dicionarios o cabeçalho sempre será as chaves do primeiro item do dicionario.
    Passar workbook em noba_aba para adicionar nova aba apos executar uma vez sem.
    Para formatar numeros enviar colunas_numero como uma tupla, onde o primeiro elemento é uma lista com a letra das colunas que serão formatadas e o segundo elemento da tupla é a quantidade casas decimais"""
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

        if cabecalho_negrito:
            negrito = Font(bold=True)
            for celula in worksheet[1]:
                celula.font = negrito

        if formatar_numero:
            colunas, casas_decimais = formatar_numero
            formato = '#,##0.' + ''.join(['0' for _ in range(casas_decimais)])
            for coluna in colunas:
                for celula in worksheet[coluna]:
                    celula.number_format = formato

        if formatar_data:
            colunas = formatar_data
            formato = 'DD/MM/YYYY'
            for coluna in colunas:
                for celula in worksheet[coluna]:
                    celula.number_format = formato

        if ajustar_largura_colunas:
            for coluna in worksheet.columns:
                maior_largura = 0
                letra_coluna = coluna[0].column_letter  # type:ignore
                for celula in coluna:
                    if celula.value:
                        maior_largura = max(maior_largura, len(str(celula.value)))
                largura_ajustada = maior_largura + 2
                worksheet.column_dimensions[letra_coluna].width = largura_ajustada

    return workbook


def salvar_excel_temporario(workbook: openpyxl.Workbook) -> BytesIO:
    """Retorna o byte stream na posição inicial com o objeto salvo"""
    byte_stream = BytesIO()
    workbook.save(byte_stream)
    byte_stream.seek(0)
    return byte_stream


def gerar_cabecalho(campos):
    """Retorna uma lista de campos, onde os campos são campos de um queryset"""
    cabecalho = [campo for campo in campos]
    return cabecalho


def gerar_conteudo_excel(queryset, cabecalho):
    """Retorna uma lista com o conteudo das linhas de uma planilha, onde o cabeçalho é uma lista de campos do queryset"""
    conteudo = []
    for obj in queryset:
        linha = [getattr(obj, field) for field in cabecalho]  # type:ignore
        conteudo.append(linha)
    return conteudo


def somar_coluna_formatada(conteudo, titulo_aba, workbook, letra_coluna_soma, cabecalho_soma):
    """Soma a coluna informada com a cor verde"""
    total_linhas = len(conteudo)

    worksheet = workbook[titulo_aba]

    verde = PatternFill(start_color='00CC00', end_color='00CC00', fill_type='solid')
    negrito = Font(bold=True)

    celula = worksheet[f'{letra_coluna_soma}{total_linhas + 2}']
    celula.value = f'=SUM({letra_coluna_soma}2:{letra_coluna_soma}{total_linhas + 1})'
    celula.number_format = '#,##0.00'
    celula.fill = verde
    celula.font = negrito

    celula = worksheet[f'{letra_coluna_soma}{total_linhas + 3}']
    celula.value = cabecalho_soma
    celula.fill = verde
    celula.font = negrito


def arquivo_excel_response(arquivo_salvo_excel, nome_arquivo):
    response = HttpResponse(
        arquivo_salvo_excel,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="{}.xlsx"'.format(nome_arquivo)
    return response
