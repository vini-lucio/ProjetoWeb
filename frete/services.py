from decimal import Decimal
from math import ceil
from frete.models import TransportadorasRegioesValores
from utils.oracle.conectar import executar_oracle
from utils.site_setup import (get_transportadoras_regioes_cidades, get_produtos, get_site_setup, get_estados_icms,
                              get_cidades)
from django.core.exceptions import ObjectDoesNotExist


def get_dados_orcamento(orcamento: int):
    """Retorna os dados de entrega para calculo de frete"""
    sql = """
        SELECT
            ORCAMENTOS.NUMPED AS ORCAMENTO,
            ORCAMENTOS.CHAVE_TRANSPORTADORA,
            CLIENTES.NOMERED AS CLIENTE,
            ORCAMENTOS.VALOR_COM_FRETE AS VALOR_TOTAL,
            JOBS.UF AS UF_ORIGEM,
            ESTADOS.SIGLA AS UF_FATURAMENTO,
            COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS2.SIGLA, ESTADOS.SIGLA) AS UF_DESTINO,
            COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE) AS CIDADE_DESTINO,
            ORCAMENTOS.DESTINO AS DESTINO_MERCADORIAS,
            CASE WHEN ORCAMENTOS.ZONA_FRANCA = 'SIM' OR ORCAMENTOS.LIVRE_COMERCIO = 'SIM' THEN 'SIM' ELSE 'NAO' END AS ZONA_FRANCA_ALC

        FROM
            (
                SELECT
                    ORCAMENTOS_ORDEM.CHAVE AS CHAVE_ORCAMENTO,
                    ESTADOS_ORDEM.SIGLA AS UF_ORDEM,
                    CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM

                FROM
                    COPLAS.ESTADOS ESTADOS_ORDEM,
                    COPLAS.ORCAMENTOS ORCAMENTOS_ORDEM,
                    COPLAS.CLIENTES CLIENTES_ORDEM

                WHERE
                    ORCAMENTOS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND
                    CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE AND

                    ORCAMENTOS_ORDEM.NUMPED = :orcamento
            ) UF_ORDEM,
            COPLAS.ESTADOS ESTADOS2,
            COPLAS.PLATAFORMAS,
            COPLAS.ESTADOS,
            COPLAS.CLIENTES,
            COPLAS.JOBS,
            COPLAS.ORCAMENTOS

        WHERE
            ORCAMENTOS.CHAVE = UF_ORDEM.CHAVE_ORCAMENTO(+) AND
            PLATAFORMAS.UF_ENT = ESTADOS2.CHAVE(+) AND
            ORCAMENTOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
            CLIENTES.CODCLI = ORCAMENTOS.CHAVE_CLIENTE AND
            ESTADOS.CHAVE = CLIENTES.UF AND
            JOBS.CODIGO = ORCAMENTOS.CHAVE_JOB AND

            ORCAMENTOS.NUMPED = :orcamento
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, orcamento=orcamento)

    if not resultado:
        raise ObjectDoesNotExist("Orçamento não existe")

    resultado = resultado[0]

    return resultado


def get_dados_pedidos_em_aberto():
    """Retorna os dados de entrega para conferencia de atendimento das transportadoras nos pedidos em aberto"""
    sql = """
        SELECT
            VENDEDORES.NOMERED AS CARTEIRA,
            PEDIDOS.NUMPED AS PEDIDO,
            PEDIDOS.CHAVE_TRANSPORTADORA,
            JOBS.UF AS UF_ORIGEM,
            ESTADOS.SIGLA AS UF_FATURAMENTO,
            COALESCE(UF_ORDEM.UF_ORDEM, ESTADOS2.SIGLA, ESTADOS.SIGLA) AS UF_DESTINO,
            COALESCE(UF_ORDEM.CIDADE_ORDEM, PLATAFORMAS.CIDADE_ENT, CLIENTES.CIDADE) AS CIDADE_DESTINO

        FROM
            (
                SELECT
                    PEDIDOS_ORDEM.CHAVE AS CHAVE_PEDIDO,
                    ESTADOS_ORDEM.SIGLA AS UF_ORDEM,
                    CLIENTES_ORDEM.CIDADE AS CIDADE_ORDEM

                FROM
                    COPLAS.ESTADOS ESTADOS_ORDEM,
                    COPLAS.PEDIDOS PEDIDOS_ORDEM,
                    COPLAS.CLIENTES CLIENTES_ORDEM

                WHERE
                    PEDIDOS_ORDEM.CHAVE_CLIENTE_REMESSA = CLIENTES_ORDEM.CODCLI AND
                    CLIENTES_ORDEM.UF = ESTADOS_ORDEM.CHAVE AND
                    PEDIDOS_ORDEM.STATUS != 'LIQUIDADO' AND
                    PEDIDOS_ORDEM.COBRANCA_FRETE IN (0, 1, 4, 5)
            ) UF_ORDEM,
            COPLAS.VENDEDORES,
            COPLAS.ESTADOS ESTADOS2,
            COPLAS.PLATAFORMAS,
            COPLAS.ESTADOS,
            COPLAS.CLIENTES,
            COPLAS.JOBS,
            COPLAS.PEDIDOS

        WHERE
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            PEDIDOS.CHAVE = UF_ORDEM.CHAVE_PEDIDO(+) AND
            PLATAFORMAS.UF_ENT = ESTADOS2.CHAVE(+) AND
            PEDIDOS.CHAVE_PLATAFORMA = PLATAFORMAS.CHAVE(+) AND
            CLIENTES.CODCLI = PEDIDOS.CHAVE_CLIENTE AND
            ESTADOS.CHAVE = CLIENTES.UF AND
            JOBS.CODIGO = PEDIDOS.CHAVE_JOB AND
            PEDIDOS.STATUS != 'LIQUIDADO' AND
            PEDIDOS.COBRANCA_FRETE IN (0, 1, 4, 5)
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    return resultado


def get_dados_itens_orcamento(orcamento: int):
    """Retorna os dados dos itens do orcamento para calculo de frete"""
    sql = """
        SELECT
            PRODUTOS.CODIGO,
            ORCAMENTOS_ITENS.CHAVE_PRODUTO,
            ORCAMENTOS_ITENS.QUANTIDADE,
            ORCAMENTOS_ITENS.ANALISE_PIS + ORCAMENTOS_ITENS.ANALISE_COFINS AS PIS_COFINS,
            ORCAMENTOS_ITENS.ANALISE_ICMS AS ICMS

        FROM
            COPLAS.PRODUTOS,
            COPLAS.ORCAMENTOS,
            COPLAS.ORCAMENTOS_ITENS

        WHERE
            ORCAMENTOS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
            ORCAMENTOS.CHAVE = ORCAMENTOS_ITENS.CHAVE_PEDIDO AND

            ORCAMENTOS.NUMPED = :orcamento
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, orcamento=orcamento)

    if not resultado:
        raise ObjectDoesNotExist("Orçamento sem itens")

    return resultado


def get_dados_notas(data_inicio, data_fim):
    """Retorna os dados dos itens do orcamento para calculo de frete"""
    sql = """
        SELECT DISTINCT
            NOTAS.DATA_SAIDA,
            VENDEDORES.NOMERED AS CARTEIRA,
            NOTAS.NF,
            ORCAMENTOS.NUMPED AS ORCAMENTO,
            CLIENTES.NOMERED,
            NOTAS.VALOR_MERCADORIAS,
            NOTAS.VALOR_TOTAL,
            NOTAS.VOLUMES_QUANTIDADE,
            NOTAS.PESO_BRUTO,
            COALESCE(NOTAS.CLI_ENT_UF, NOTAS.CLI_UF) AS UF_ENTREGA,
            COALESCE(NOTAS.CLI_ENT_CIDADE, NOTAS.CLI_CIDADE) AS CIDADE_ENTREGA,
            TRANSPORTADORAS.NOMERED AS TRANSPORTADORA,
            CASE WHEN NOTAS.COBRANCA_FRETE IN (0, 1, 4, 5) THEN 'REMETENTE' WHEN NOTAS.COBRANCA_FRETE IN (2, 6) THEN 'DESTINATARIO' ELSE 'INCORRETO' END AS FRETE,
            NOTAS.VALOR_FRETE AS FRETE_NOTA
            -- , JOBS.UF AS UF_ORIGEM

        FROM
            COPLAS.VENDEDORES,
            COPLAS.ORCAMENTOS,
            COPLAS.PEDIDOS,
            COPLAS.NOTAS_ITENS,
            COPLAS.TRANSPORTADORAS,
            COPLAS.NOTAS,
            COPLAS.JOBS,
            COPLAS.CLIENTES

        WHERE
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
            TRANSPORTADORAS.CODTRANSP = NOTAS.CHAVE_TRANSPORTADORA AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
            PEDIDOS.CHAVE = NOTAS_ITENS.NUMPED AND
            JOBS.CODIGO = NOTAS.CHAVE_JOB AND
            ORCAMENTOS.CHAVE = PEDIDOS.CHAVE_ORCAMENTO AND

            NOTAS.DATA_EMISSAO >= :data_inicio AND
            NOTAS.DATA_EMISSAO <= :data_fim

            -- NOTAS.DATA_EMISSAO >= TO_DATE(:data_inicio,'DD-MM-YYYY') AND
            -- NOTAS.DATA_EMISSAO <= TO_DATE(:data_fim,'DD-MM-YYYY')

        ORDER BY
            TRANSPORTADORAS.NOMERED, NOTAS.NF
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, data_fim=data_fim)

    return resultado


def get_dados_notas_monitoramento(data_inicio, data_fim):
    """Retorna os dados dos itens do orcamento para calculo de frete"""
    sql = """
        SELECT DISTINCT
            TRANSPORTADORAS.CODTRANSP,
            ORCAMENTOS.NUMPED AS ORCAMENTO,
            NOTAS.DATA_DESPACHO,
            NOTAS.NF,
            CLIENTES.NOMERED,
            COALESCE(NOTAS.CLI_ENT_UF, NOTAS.CLI_UF) AS UF_ENTREGA,
            COALESCE(NOTAS.CLI_ENT_CIDADE, NOTAS.CLI_CIDADE) AS CIDADE_ENTREGA,
            TRANSPORTADORAS.NOMERED AS TRANSPORTADORA,
            CASE WHEN NOTAS.COBRANCA_FRETE = 1 THEN 'COM COBRANCA' ELSE 'SEM COBRANCA' END AS FRETE

        FROM
            COPLAS.VENDEDORES,
            COPLAS.ORCAMENTOS,
            COPLAS.PEDIDOS,
            COPLAS.NOTAS_ITENS,
            COPLAS.TRANSPORTADORAS,
            COPLAS.NOTAS,
            COPLAS.CLIENTES

        WHERE
            VENDEDORES.CODVENDEDOR = CLIENTES.CHAVE_VENDEDOR3 AND
            CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE AND
            TRANSPORTADORAS.CODTRANSP = NOTAS.CHAVE_TRANSPORTADORA AND
            NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA AND
            PEDIDOS.CHAVE = NOTAS_ITENS.NUMPED AND
            ORCAMENTOS.CHAVE = PEDIDOS.CHAVE_ORCAMENTO AND
            NOTAS.COBRANCA_FRETE IN (0, 1) AND
            TRANSPORTADORAS.CODTRANSP NOT IN (8003, 8475, 7738, 6766, 7733, 8264) AND
            COALESCE(NOTAS.CLI_ENT_CIDADE, NOTAS.CLI_CIDADE) != 'EXTERIOR' AND

            NOTAS.DATA_DESPACHO >= :data_inicio AND
            NOTAS.DATA_DESPACHO <= :data_fim

        ORDER BY
            NOTAS.NF
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True, data_inicio=data_inicio, data_fim=data_fim)

    return resultado


def get_transportadoras_valores_atendimento(*, orcamento: int = 0, dados_orcamento_pedido=[], zona_rural: bool = False, transportadora_orcamento_pedido: bool = False) -> list[TransportadorasRegioesValores]:
    """Passar somente um dos parametros de orçamento. Retorna os dados dos valores das transportadoras que atendem o destino do orçamento informado"""
    if orcamento != 0:
        dados_orcamento_pedido = get_dados_orcamento(orcamento)

    uf_faturamento = dados_orcamento_pedido['UF_FATURAMENTO']  # type:ignore
    uf_origem = dados_orcamento_pedido['UF_ORIGEM']  # type:ignore
    uf_destino = dados_orcamento_pedido['UF_DESTINO']  # type:ignore
    cidade_destino = dados_orcamento_pedido['CIDADE_DESTINO']  # type:ignore

    faturamento_diferente_destino = uf_faturamento != uf_destino

    if not transportadora_orcamento_pedido:
        ativos_origem_destino = TransportadorasRegioesValores.filter_ativos().filter(
            transportadora_origem_destino__estado_origem_destino__uf_origem__sigla=uf_origem,
            transportadora_origem_destino__estado_origem_destino__uf_destino__sigla=uf_destino,
        )
    else:
        transportadora = dados_orcamento_pedido['CHAVE_TRANSPORTADORA']  # type:ignore
        ativos_origem_destino = TransportadorasRegioesValores.filter_ativos().filter(
            transportadora_origem_destino__estado_origem_destino__uf_origem__sigla=uf_origem,
            transportadora_origem_destino__estado_origem_destino__uf_destino__sigla=uf_destino,
            transportadora_origem_destino__transportadora__chave_analysis=transportadora,
        )

    if faturamento_diferente_destino:
        ativos_origem_destino = ativos_origem_destino.filter(
            transportadora_origem_destino__transportadora__entrega_uf_diferente_faturamento=True
        )
    if zona_rural:
        ativos_origem_destino = ativos_origem_destino.filter(
            atendimento_zona_rural=True
        )

    confere_cidade_destino = get_cidades().filter(nome=cidade_destino, estado__sigla=uf_destino).first()
    if not confere_cidade_destino:
        raise ObjectDoesNotExist('Cidade não existe')

    transportadoras_regioes_cidades = get_transportadoras_regioes_cidades().filter(
        transportadora_regiao_valor__in=ativos_origem_destino,
        transportadora_regiao_valor__atendimento_cidades_especificas=True,
        cidade=confere_cidade_destino,
    )

    valores = []
    transportadoras_cidades_id = []

    if transportadoras_regioes_cidades:
        valores = [cidade.transportadora_regiao_valor for cidade in transportadoras_regioes_cidades]
        transportadoras_cidades_id = transportadoras_regioes_cidades.values_list(
            'transportadora_regiao_valor__transportadora_origem_destino__transportadora__id',
            flat=True,
        )

    transportadoras_regioes_todas_cidades = ativos_origem_destino.filter(
        atendimento_cidades_especificas=False
    )
    if transportadoras_cidades_id:
        transportadoras_regioes_todas_cidades = transportadoras_regioes_todas_cidades.exclude(
            transportadora_origem_destino__transportadora__id__in=transportadoras_cidades_id
        )

    if transportadoras_regioes_todas_cidades:
        for valor in transportadoras_regioes_todas_cidades:
            valores.append(valor)

    if not valores:
        raise ObjectDoesNotExist('Destino não atendido')

    return valores


def get_cidades_prazo_taxas(transportadora_regiao_valor: TransportadorasRegioesValores, cidade_destino: str, uf_cidade_destino: str):
    """Retorna prazos de entrega e taxas das cidades por transportadoras"""
    taxa_cidade = 0
    prazo_tipo = transportadora_regiao_valor.prazo_tipo
    prazo = transportadora_regiao_valor.prazo_padrao
    frequencia = transportadora_regiao_valor.frequencia_padrao
    observacoes_prazo = transportadora_regiao_valor.observacoes_prazo_padrao
    cif = False

    transportadora_regiao_cidade = get_transportadoras_regioes_cidades().filter(
        transportadora_regiao_valor=transportadora_regiao_valor,
        transportadora_regiao_valor__atendimento_cidades_especificas=True,
        cidade__nome=cidade_destino,
        cidade__estado__sigla=uf_cidade_destino,
    ).first()

    if transportadora_regiao_cidade:
        cidade_taxa_cidade = transportadora_regiao_cidade.taxa
        cidade_prazo_tipo = transportadora_regiao_cidade.prazo_tipo
        cidade_prazo = transportadora_regiao_cidade.prazo
        cidade_frequencia = transportadora_regiao_cidade.frequencia
        cidade_observacoes_prazo = transportadora_regiao_cidade.observacoes
        cidade_cif = transportadora_regiao_cidade.cif

        taxa_cidade = cidade_taxa_cidade if cidade_taxa_cidade != 0 else taxa_cidade
        prazo_tipo = cidade_prazo_tipo if cidade_prazo_tipo else prazo_tipo
        prazo = cidade_prazo if cidade_prazo != 0 else prazo
        frequencia = cidade_frequencia if cidade_frequencia else frequencia
        observacoes_prazo = cidade_observacoes_prazo if cidade_observacoes_prazo else observacoes_prazo
        cif = cidade_cif if cidade_cif else cif

    prazo = {'taxa_cidade': taxa_cidade, 'prazo_tipo': prazo_tipo, 'prazo': prazo, 'frequencia': frequencia,
             'observacoes_prazo': observacoes_prazo, 'cif': cif, }

    return prazo


def get_prazos(uf_origem: str, uf_destino: str, cidade_destino: str) -> list[dict]:
    """Retorna os prazos por transportadora de uma origem e cidade destino especifica"""
    dados = {
        'UF_ORIGEM': uf_origem,
        'UF_DESTINO': uf_destino,
        'CIDADE_DESTINO': cidade_destino,
    }
    dados.update({'UF_FATURAMENTO': dados['UF_DESTINO']})

    prazos = []
    valores = get_transportadoras_valores_atendimento(dados_orcamento_pedido=dados)
    for valor in valores:
        prazo = get_cidades_prazo_taxas(valor, cidade_destino, uf_destino)
        prazo.update({'transportadora': valor, 'uf_origem': uf_origem, 'uf_destino': uf_destino,
                      'cidade_destino': cidade_destino})
        prazos.append(prazo)

    return prazos


def get_dados_itens_frete(dados_itens_orcamento):
    """Retorna uma tupla com os dados de volume dos produtos, pis/cofins e icms"""
    dados_itens = []
    produtos = get_produtos()
    pis_cofins_orc = Decimal(0)
    icms_orc = Decimal(0)

    for item_orcamento in dados_itens_orcamento:
        id_produto_orc = item_orcamento['CHAVE_PRODUTO']  # type:ignore
        quantidade_produto_orc = Decimal(item_orcamento['QUANTIDADE'])  # type:ignore
        pis_cofins_orc = Decimal(item_orcamento['PIS_COFINS'])  # type:ignore
        icms_orc = Decimal(item_orcamento['ICMS'])  # type:ignore

        try:
            produto = produtos.get(chave_analysis=id_produto_orc)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist('Produto não cadastrado')
        peso_liquido = produto.peso_liquido
        peso_bruto = produto.peso_bruto
        quantidade_volume = produto.quantidade_volume
        m3_volume = produto.m3_volume

        maior_peso = peso_liquido if peso_liquido >= peso_bruto else peso_bruto
        peso = maior_peso * quantidade_produto_orc

        volumes = quantidade_produto_orc / quantidade_volume

        m3 = volumes * m3_volume

        item = {'produto': produto, 'peso_item': peso, 'volumes_item': volumes, 'm3_item': m3}
        dados_itens.append(item)

    return dados_itens, pis_cofins_orc, icms_orc


def calcular_frete(orcamento: int, zona_rural: bool = False, *, transportadora_orcamento_pedido: bool = False, transportadora_regiao_valor_especifico: TransportadorasRegioesValores | None = None):
    """Retorna uma tupla com os valores do frete por transportadora, dados do orçamento, dados dos itens do orcamento e dados dos volumes dos itens. Se transportadora região valor especifico for informado, será calculado independente do destino do orçamento"""
    dados_orcamento = get_dados_orcamento(orcamento)
    dados_itens_orcamento = get_dados_itens_orcamento(orcamento)
    fretes = []

    valor_total_orc = Decimal(dados_orcamento['VALOR_TOTAL'])  # type:ignore
    destino_consumo_orc = True if dados_orcamento['DESTINO_MERCADORIAS'] == 'CONSUMO' else False  # type:ignore
    # zona_franca_alc_orc = True if dados_orcamento['ZONA_FRANCA_ALC'] == 'SIM' else False  # type:ignore
    uf_origem_orc = dados_orcamento['UF_ORIGEM']  # type:ignore
    uf_destino_orc = dados_orcamento['UF_DESTINO']  # type:ignore
    cidade_destino_orc = dados_orcamento['CIDADE_DESTINO']  # type:ignore

    dados_itens, pis_cofins_orc, icms_orc = get_dados_itens_frete(dados_itens_orcamento)

    dados_volume = {}
    valores = []
    if not transportadora_regiao_valor_especifico:
        valores = get_transportadoras_valores_atendimento(dados_orcamento_pedido=dados_orcamento,
                                                          zona_rural=zona_rural,
                                                          transportadora_orcamento_pedido=transportadora_orcamento_pedido)
    else:
        valores.append(transportadora_regiao_valor_especifico)

    if valores:
        site_setup = get_site_setup()
        if site_setup:
            aliquota_pis_cofins = site_setup.aliquota_pis_cofins / 100
            if pis_cofins_orc == 0:
                aliquota_pis_cofins = Decimal(3.08 / 100)  # 2% IR + 1,08% CSLL
            aliquota_icms_simples = site_setup.aliquota_icms_simples / 100

        for valor in valores:
            razao = valor.razao
            total_peso_maior = 0
            total_peso_real = 0
            total_volumes = 0
            total_m3 = 0
            for item in dados_itens:
                total_volumes += item['volumes_item']
                total_m3 += item['m3_item']

                peso_cubado = item['m3_item'] * razao
                peso_maior = peso_cubado if peso_cubado >= item['peso_item'] else item['peso_item']
                total_peso_maior += peso_maior
                total_peso_real += item['peso_item']
            total_volumes = ceil(total_volumes)
            dados_volume = {'total_volumes': total_volumes, 'total_m3': round(total_m3, 4),
                            'total_peso_real': round(total_peso_real, 2)}

            margens = valor.transportadorasregioesmargens.all().order_by('-ate_kg')  # type:ignore
            maior_margem_kg = 0
            maior_margem_valor = 0
            if margens.first():
                maior_margem_kg = margens.first().ate_kg
                maior_margem_valor = margens.first().valor
            passou_margem = False
            if total_peso_maior > maior_margem_kg:
                passou_margem = True
            if not passou_margem:
                for margem in margens:
                    if total_peso_maior > margem.ate_kg:
                        break
                    maior_margem_kg = margem.ate_kg
                    maior_margem_valor = margem.valor
            valor_kg = valor.valor_kg
            kg_excedente = valor.valor_kg_excedente
            frete_peso = maior_margem_valor
            if passou_margem:
                frete_peso = valor_kg * total_peso_maior
                if kg_excedente:
                    frete_peso = maior_margem_valor + (valor_kg * (total_peso_maior - maior_margem_kg))

            advaloren = valor.advaloren / 100
            advaloren_minimo = valor.advaloren_valor_minimo
            valor_advaloren = valor_total_orc * advaloren
            if valor_advaloren < advaloren_minimo:
                valor_advaloren = advaloren_minimo

            gris = valor.gris / 100
            gris_minimo = valor.gris_valor_minimo
            valor_gris = valor_total_orc * gris
            if valor_gris < gris_minimo:
                valor_gris = gris_minimo

            taxa_coleta = valor.taxa_coleta
            taxa_conhecimento = valor.taxa_conhecimento
            taxa_sefaz = valor.taxa_sefaz
            taxa_suframa = valor.taxa_suframa

            pedagio_fracao = valor.pedagio_fracao
            pedagio_fracao_valor = valor.pedagio_valor_fracao
            pedagio_minimo = valor.pedagio_valor_minimo
            valor_pedagio = 0
            if pedagio_fracao != 0:
                fracoes = ceil(total_peso_maior / pedagio_fracao)
                valor_pedagio = fracoes * pedagio_fracao_valor
            if valor_pedagio < pedagio_minimo:
                valor_pedagio = pedagio_minimo

            taxa_frete_peso = valor.taxa_frete_peso / 100
            taxa_frete_peso_minimo = valor.taxa_frete_peso_valor_minimo
            valor_taxa_frete_peso = frete_peso * taxa_frete_peso
            if valor_taxa_frete_peso < taxa_frete_peso_minimo:
                valor_taxa_frete_peso = taxa_frete_peso_minimo

            taxa_valor_nota = valor.taxa_valor_nota / 100
            taxa_valor_nota_minimo = valor.taxa_valor_nota_valor_minimo
            valor_taxa_valor_nota = valor_total_orc * taxa_valor_nota
            if valor_taxa_valor_nota < taxa_valor_nota_minimo:
                valor_taxa_valor_nota = taxa_valor_nota_minimo

            taxa_zona_rural = 0
            if zona_rural:
                taxa_zona_rural = valor.taxa_zona_rural

            dados_cidade_prazo = get_cidades_prazo_taxas(valor, cidade_destino_orc, uf_destino_orc)
            taxa_cidade = dados_cidade_prazo['taxa_cidade']
            prazo_tipo = dados_cidade_prazo['prazo_tipo']
            prazo = dados_cidade_prazo['prazo']
            frequencia = dados_cidade_prazo['frequencia']
            observacoes_prazo = dados_cidade_prazo['observacoes_prazo']
            cif = dados_cidade_prazo['cif']

            valor_frete_liquido = (
                frete_peso + valor_advaloren + valor_gris + taxa_coleta + taxa_conhecimento +
                taxa_sefaz + taxa_suframa + valor_pedagio + valor_taxa_frete_peso + valor_taxa_valor_nota +
                taxa_zona_rural + taxa_cidade
            )
            frete_minimo = valor.frete_minimo_valor
            frete_minimo_percentual = valor.frete_minimo_percentual / 100 * valor_total_orc
            if frete_minimo < frete_minimo_percentual:
                frete_minimo = frete_minimo_percentual
            if valor_frete_liquido < frete_minimo:
                valor_frete_liquido = frete_minimo

            aliquota_icms_frete = valor.transportadora_origem_destino.estado_origem_destino.icms_frete / 100
            simples_nacional = valor.transportadora_origem_destino.transportadora.simples_nacional
            if simples_nacional:
                aliquota_icms_frete = aliquota_icms_simples
            aliquota_icms_frete_por_dentro = 1 - aliquota_icms_frete

            valor_frete_empresa = valor_frete_liquido / aliquota_icms_frete_por_dentro
            valor_icms_frete = valor_frete_empresa * aliquota_icms_frete

            aliquota_icms = valor.transportadora_origem_destino.estado_origem_destino.icms / 100
            credito_icms = valor_icms_frete
            if destino_consumo_orc:
                icms_interno = get_estados_icms().get(uf_origem__sigla=uf_origem_orc, uf_destino__sigla=uf_origem_orc)
                icms_interno = icms_interno.icms / 100
                aliquota_icms = icms_interno
            if icms_orc == 0:
                aliquota_icms = 0
            if icms_orc == 0 or simples_nacional:
                credito_icms = 0
            aliquota_impostos_totais = aliquota_icms + aliquota_pis_cofins
            aliquota_impostos_totais_por_dentro = 1 - aliquota_impostos_totais

            valor_frete_cliente = (valor_frete_empresa - credito_icms) / aliquota_impostos_totais_por_dentro

            frete = {
                'valor': valor,
                'valor_frete_empresa': round(valor_frete_empresa, 2),
                'valor_frete_cliente': round(valor_frete_cliente, 2),
                'prazo_tipo': prazo_tipo,
                'prazo': prazo,
                'frequencia': frequencia,
                'observacoes_prazo': observacoes_prazo,
                'cif': cif,
                'total_peso_maior': round(total_peso_maior, 2),
            }
            fretes.append(frete)

    return fretes, dados_orcamento, dados_itens_orcamento, dados_volume
