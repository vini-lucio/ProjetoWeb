from analysis.models import PEDIDOS_ITENS
from .services_producao import get_relatorios_producao
from django.db.models import F
from utils.data_hora_atual import data_x_dias
from utils.oracle.conectar import executar_oracle
import pandas as pd


class DashBoardPcp():
    """Gera dashboard de PCP."""

    def __init__(self, chave_familia_produto, local) -> None:
        data_limite_futuro = data_x_dias(4, False)

        pedidos_estoque_negativo = PEDIDOS_ITENS.objects.values(
            'DATA_ENTREGA', 'QUANTIDADE', PEDIDO=F('CHAVE_PEDIDO__NUMPED'), PRODUTO=F('CHAVE_PRODUTO__CODIGO'),
            ESTOQUE_DISPONIVEL=F('CHAVE_PRODUTO__ESTOQUE_DISPONIVEL'), ESTOQUE_ATUAL=F('CHAVE_PRODUTO__ESTOQUE_ATUAL'),
        ).filter(
            CHAVE_PRODUTO__ESTOQUE_DISPONIVEL__lt=0, CHAVE_PRODUTO__CHAVE_FAMILIA=7766,
            QUANTIDADE__gt=F('CHAVE_PRODUTO__ESTOQUE_ATUAL'), DATA_ENTREGA__lte=data_limite_futuro,
        ).exclude(CHAVE_PEDIDO__STATUS='LIQUIDADO').order_by('DATA_ENTREGA')
        dt_pedidos_estoque_negativo = pd.DataFrame(pedidos_estoque_negativo)

        if not dt_pedidos_estoque_negativo.empty:
            injetado_aberto = get_relatorios_producao(status_ordem_producao_em_aberto=True,
                                                      coluna_producao_liquida=True, coluna_produto=True,
                                                      familia_produto=7766, setor=3)
            dt_injetado_aberto = pd.DataFrame(injetado_aberto)
            dt_injetado_aberto = dt_injetado_aberto.drop(columns=['HORAS_APONTADAS'])
            dt_injetado_aberto = dt_injetado_aberto.rename(columns={'PRODUCAO_LIQUIDA': 'INJETADO'})

            embalado_aberto = get_relatorios_producao(status_ordem_producao_em_aberto=True,
                                                      coluna_producao_liquida=True, coluna_produto=True,
                                                      familia_produto=7766, setor=12)
            dt_embalado_aberto = pd.DataFrame(embalado_aberto)
            dt_embalado_aberto = dt_embalado_aberto.drop(columns=['HORAS_APONTADAS'])
            dt_embalado_aberto = dt_embalado_aberto.rename(columns={'PRODUCAO_LIQUIDA': 'EMBALADO'})

            # TODO: trocar a embalar quando implementar novo sistema de embalagem?
            dt_a_embalar = pd.merge(dt_injetado_aberto, dt_embalado_aberto, 'left', 'PRODUTO').fillna(0)
            dt_a_embalar['A_EMBALAR'] = dt_a_embalar['INJETADO'] - dt_a_embalar['EMBALADO']

            dt_pedidos_estoque_negativo = pd.merge(dt_pedidos_estoque_negativo, dt_a_embalar,
                                                   'left', 'PRODUTO').fillna(0)

            self.pedidos_estoque_negativo = dt_pedidos_estoque_negativo.to_dict(orient='records')

            self.demanda = demanda_produtos(chave_familia_produto, local)


# TODO: get_relatorio_xxx ou filter django
def demanda_produtos(chave_familia_produto, local) -> list | None:
    """Retorna a demanda a ser produzida com prioridades.

    Parametros:
    -----------
    :chave_familia_produto [int]: com a chave da familia de produtos a ser filtrada.
    :local [str]: com a local a pesquisar produtos 'Em Estoque' ou 'Em Maquina'.

    Retorno:
    --------
    :list[dict]: com a demanda de produtos."""
    filtro_op = ''
    order_by = """
        ORDER BY STATUS,
            CASE
                WHEN HORAS_UTEIS_PRODUCAO > 0 THEN 0
                ELSE 1
            END,
            CASE
                WHEN DEMANDA_DISPONIVEL < 0 THEN 0
                ELSE 1
            END,
            CASE
                WHEN ESTOQUE_RESERVADO > 0 THEN 0
                ELSE 1
            END,
            P,
            DEMANDA_DISPONIVEL
    """
    if chave_familia_produto == 7766:
        em_maquina = "NOT"
        if local == 'Em Maquina':
            em_maquina = ""
            order_by = """
                ORDER BY DEMANDA_DISPONIVEL DESC,
                    P DESC
            """

        filtro_op = """
            AND PRODUTOS.CPROD {em_maquina} IN (
                SELECT DISTINCT CHAVE_PRODUTO
                FROM COPLAS.ORDENS
                WHERE STATUS NOT IN ('FECHADA', 'CANCELADA')
            )
        """.format(em_maquina=em_maquina)

    sql = """
        SELECT CASE
                WHEN ABC = 'A' THEN 1
                WHEN ABC = 'B' THEN 2
                WHEN ABC = 'C'
                AND IND LIKE 'IND%' THEN 3
                ELSE 4
            END AS P,
            ABC,
            IND,
            CODIGO,
            UNIDADE,
            QUANTIDADE_MEDIANA_SEM_0 AS QUANTIDADE_MEDIANA,
            ESTOQUE_ATUAL,
            ESTOQUE_DISPONIVEL,
            ESTOQUE_RESERVADO,
            COALESCE(PP_MP_PROCESSO, 0) AS PP_MP_PROCESSO,
            PROXIMA_ENTREGA,
            ULTIMA_ENTREGA,
            CASE
                WHEN QUANTIDADE_MEDIANA_SEM_0 = 0 THEN CASE
                    WHEN ESTOQUE_DISPONIVEL < 0 THEN 0
                    ELSE 1
                END
                ELSE (
                    ESTOQUE_DISPONIVEL - COALESCE(PP_MP_PROCESSO, 0)
                ) / QUANTIDADE_MEDIANA_SEM_0
            END * 100 AS DEMANDA_DISPONIVEL,
            CASE
                WHEN QUANTIDADE_MEDIANA_SEM_0 < ESTOQUE_DISPONIVEL THEN 0
                ELSE QUANTIDADE_MEDIANA_SEM_0 - ESTOQUE_DISPONIVEL + COALESCE(PP_MP_PROCESSO, 0)
            END A_PRODUZIR,
            CASE
                WHEN QUANTIDADE_MEDIANA_SEM_0 < ESTOQUE_DISPONIVEL THEN 0
                ELSE QUANTIDADE_MEDIANA_SEM_0 - ESTOQUE_DISPONIVEL + COALESCE(PP_MP_PROCESSO, 0)
            END * HORAS_PRODUCAO AS HORAS_UTEIS_PRODUCAO,
            CASE
                WHEN ESTOQUE_DISPONIVEL - COALESCE(PP_MP_PROCESSO, 0) < 0 THEN '0 NEGATIVO URGENTE ENTRAR EM MAQUINA'
                WHEN CASE
                    WHEN QUANTIDADE_MEDIANA_SEM_0 = 0 THEN CASE
                        WHEN ESTOQUE_DISPONIVEL < 0 THEN 0
                        ELSE 1
                    END
                    ELSE (
                        ESTOQUE_DISPONIVEL - COALESCE(PP_MP_PROCESSO, 0)
                    ) / QUANTIDADE_MEDIANA_SEM_0
                END * 100 <= 10 THEN '1 URGENTE ENTRAR EM MAQUINA'
                WHEN CASE
                    WHEN QUANTIDADE_MEDIANA_SEM_0 = 0 THEN CASE
                        WHEN ESTOQUE_DISPONIVEL < 0 THEN 0
                        ELSE 1
                    END
                    ELSE (
                        ESTOQUE_DISPONIVEL - COALESCE(PP_MP_PROCESSO, 0)
                    ) / QUANTIDADE_MEDIANA_SEM_0
                END * 100 < 50 THEN '2 ENTRAR EM MAQUINA'
            END AS STATUS
        FROM (
                SELECT PERIODO.ABC,
                    PERIODO.IND,
                    PERIODO.CODIGO,
                    PERIODO.ESTOQUE_ATUAL,
                    PERIODO.ESTOQUE_DISPONIVEL,
                    PERIODO.ESTOQUE_RESERVADO,
                    PERIODO.UNIDADE,
                    CASE
                        WHEN (
                            PERIODO.ABC = 'C'
                            AND SUM(
                                CASE
                                    WHEN MED.QUANTIDADE IS NULL
                                    OR MED.QUANTIDADE = 0 THEN 1
                                    ELSE 0
                                END
                            ) >= 4
                        )
                        OR PERIODO.ESTRATEGICO = 'ESTRATEGICO' THEN 0
                        ELSE MEDIAN(MED.QUANTIDADE)
                    END AS QUANTIDADE_MEDIANA_SEM_0,
                    PERIODO.PROXIMA_ENTREGA,
                    PERIODO.ULTIMA_ENTREGA,
                    PERIODO.HORAS_PRODUCAO
                FROM (
                        SELECT CASE
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A'
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B'
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C'
                                ELSE 'C'
                            END AS ABC,
                            CASE
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%INDUSTRIA A%' THEN 'IND A'
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%INDUSTRIA B%' THEN 'IND B'
                            END AS IND,
                            CASE
                                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTRATEGICO%' THEN 'ESTRATEGICO'
                            END AS ESTRATEGICO,
                            PRODUTOS.CODIGO,
                            PRODUTOS.ESTOQUE_ATUAL,
                            PRODUTOS.ESTOQUE_DISPONIVEL,
                            PRODUTOS.ESTOQUE_RESERVADO,
                            PERIODO.MES_ANO,
                            UNIDADES.UNIDADE,
                            PEDIDOS.PROXIMA_ENTREGA,
                            PEDIDOS.ULTIMA_ENTREGA,
                            HORAS_PRODUCAO.HORAS_PRODUCAO
                        FROM (
                                SELECT PROCESSOS.CHAVE_PRODUTO,
                                    PROCESSOS_OPERACOES.TEMPO_TOTAL / 60 / 60 AS HORAS_PRODUCAO
                                FROM COPLAS.PROCESSOS,
                                    COPLAS.PROCESSOS_OPERACOES
                                WHERE PROCESSOS.CHAVE = PROCESSOS_OPERACOES.CHAVE_PROCESSO
                                    AND PROCESSOS_OPERACOES.CHAVE_SETOR = 3
                                    AND PROCESSOS.PADRAO = 'SIM'
                            ) HORAS_PRODUCAO,
                            (
                                SELECT PEDIDOS_ITENS.CHAVE_PRODUTO,
                                    MIN(PEDIDOS_ITENS.DATA_ENTREGA) AS PROXIMA_ENTREGA,
                                    MAX(PEDIDOS_ITENS.DATA_ENTREGA) AS ULTIMA_ENTREGA
                                FROM COPLAS.PEDIDOS,
                                    COPLAS.PEDIDOS_ITENS
                                WHERE PEDIDOS.CHAVE = PEDIDOS_ITENS.CHAVE_PEDIDO
                                    AND EXISTS(
                                        SELECT CHAVE
                                        FROM COPLAS.PEDIDOS_TIPOS
                                        WHERE VALOR_COMERCIAL = 'SIM'
                                            AND CHAVE = PEDIDOS.CHAVE_TIPO
                                    )
                                    AND PEDIDOS.STATUS != 'LIQUIDADO'
                                GROUP BY PEDIDOS_ITENS.CHAVE_PRODUTO
                            ) PEDIDOS,
                            COPLAS.UNIDADES,
                            COPLAS.PRODUTOS,
                            (
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-12' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-12' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-11' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-11' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-10' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-10' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-9' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-9' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-8' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-8' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-7' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-7' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-6' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-6' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-5' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-5' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-4' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-4' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-3' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-3' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-2' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-2' MONTH) AS MES_ANO FROM DUAL UNION ALL
                                SELECT EXTRACT(MONTH FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-1' MONTH) || '-' || EXTRACT(YEAR FROM TRUNC(SYSDATE, 'MM') + INTERVAL '-1' MONTH) AS MES_ANO FROM DUAL
                            ) PERIODO
                        WHERE PRODUTOS.CPROD = HORAS_PRODUCAO.CHAVE_PRODUTO(+)
                            AND PRODUTOS.CPROD = PEDIDOS.CHAVE_PRODUTO(+)
                            AND PRODUTOS.CHAVE_UNIDADE = UNIDADES.CHAVE
                            AND PRODUTOS.CHAVE_FAMILIA = :chave_familia_produto
                            AND PRODUTOS.FORA_DE_LINHA = 'NAO'
                            AND PRODUTOS.DESENVOLVIMENTO = 'NAO'
                            AND PRODUTOS.CODIGO NOT LIKE 'KIT %'
                            AND PRODUTOS.CODIGO NOT LIKE 'AMOSTRA%'
                            AND PRODUTOS.CODIGO NOT LIKE 'CHAVEIRO%'
                            AND PRODUTOS.CODIGO NOT LIKE 'MA500-35  - _M%'
                            AND PRODUTOS.CODIGO NOT LIKE 'MA500-35  - _,_%'
                            AND PRODUTOS.CODIGO NOT LIKE 'TRY-OUT'
                            AND PRODUTOS.CHAVE_GRUPO NOT IN (10819, 12217)
                            {filtro_op}
                    ) PERIODO,
                    (
                        SELECT PRODUTOS.CODIGO,
                            EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) || '-' || EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO) AS MES_ANO,
                            SUM(NOTAS_ITENS.QUANTIDADE) AS QUANTIDADE,
                            UNIDADES.UNIDADE
                        FROM COPLAS.UNIDADES,
                            COPLAS.CLIENTES,
                            COPLAS.NOTAS,
                            COPLAS.NOTAS_ITENS,
                            COPLAS.PRODUTOS
                        WHERE UNIDADES.CHAVE = PRODUTOS.CHAVE_UNIDADE
                            AND CLIENTES.CODCLI = NOTAS.CHAVE_CLIENTE
                            AND NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA
                            AND NOTAS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD
                            AND NOTAS.VALOR_COMERCIAL = 'SIM'
                            AND NOTAS.ESPECIE = 'S'
                            AND PRODUTOS.CHAVE_FAMILIA = :chave_familia_produto
                            AND PRODUTOS.FORA_DE_LINHA = 'NAO'
                            AND PRODUTOS.DESENVOLVIMENTO = 'NAO'
                            AND PRODUTOS.CODIGO NOT LIKE 'KIT %'
                            AND PRODUTOS.CODIGO NOT LIKE 'AMOSTRA%'
                            AND PRODUTOS.CODIGO NOT LIKE 'CHAVEIRO%'
                            AND PRODUTOS.CODIGO NOT LIKE 'MA500-35  - _M%'
                            AND PRODUTOS.CODIGO NOT LIKE 'MA500-35  - _,_%'
                            AND PRODUTOS.CODIGO NOT LIKE 'TRY-OUT'
                            AND PRODUTOS.CHAVE_GRUPO NOT IN (10819, 12217)
                            {filtro_op}
                            AND NOTAS.DATA_EMISSAO >= TRUNC(SYSDATE, 'MM') - INTERVAL '12' MONTH
                            AND NOTAS.DATA_EMISSAO <= LAST_DAY(TRUNC(SYSDATE, 'MM') - INTERVAL '1' MONTH)
                        GROUP BY PRODUTOS.CODIGO,
                            EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) || '-' || EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO),
                            UNIDADES.UNIDADE
                    ) MED
                WHERE PERIODO.CODIGO = MED.CODIGO(+)
                    AND PERIODO.MES_ANO = MED.MES_ANO(+)
                GROUP BY PERIODO.ABC,
                    PERIODO.IND,
                    PERIODO.ESTRATEGICO,
                    PERIODO.CODIGO,
                    PERIODO.ESTOQUE_ATUAL,
                    PERIODO.ESTOQUE_DISPONIVEL,
                    PERIODO.ESTOQUE_RESERVADO,
                    PERIODO.UNIDADE,
                    PERIODO.PROXIMA_ENTREGA,
                    PERIODO.ULTIMA_ENTREGA,
                    PERIODO.HORAS_PRODUCAO
            ) PROD,
            (
                SELECT CPROD AS PP_MP_CPROD,
                    CODIGO AS PP_MP_CODIGO,
                    CASE
                        WHEN QUANTIDADE_MEDIANA_SEM_0 IS NULL
                        OR QUANTIDADE_MEDIANA_SEM_0 < ESTOQUE_DISPONIVEL THEN 0
                        ELSE QUANTIDADE_MEDIANA_SEM_0 - ESTOQUE_DISPONIVEL
                    END PP_MP_PROCESSO
                FROM (
                        SELECT PERIODO.CPROD,
                            PERIODO.CODIGO,
                            CASE
                                WHEN (
                                    PERIODO.ABC = 'C'
                                    AND SUM(
                                        CASE
                                            WHEN MED.QUANTIDADE IS NULL
                                            OR MED.QUANTIDADE = 0 THEN 1
                                            ELSE 0
                                        END
                                    ) >= 4
                                )
                                OR PERIODO.ESTRATEGICO = 'ESTRATEGICO' THEN 0
                                ELSE MEDIAN(MED.QUANTIDADE)
                            END AS QUANTIDADE_MEDIANA_SEM_0,
                            PERIODO.ESTOQUE_DISPONIVEL
                        FROM (
                                SELECT PRODUTOS.CPROD,
                                    PRODUTOS.CODIGO,
                                    CASE
                                        WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A'
                                        WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B'
                                        WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C'
                                        ELSE 'C'
                                    END AS ABC,
                                    CASE
                                        WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTRATEGICO%' THEN 'ESTRATEGICO'
                                    END AS ESTRATEGICO,
                                    PRODUTOS.ESTOQUE_DISPONIVEL * PRODUTOS.QUANTIDADE AS ESTOQUE_DISPONIVEL
                                FROM (
                                        SELECT DISTINCT PRODUTOS.CPROD,
                                            MATERIAIS.CODIGO,
                                            PRODUTOS.CARACTERISTICA2,
                                            PRODUTOS.ESTOQUE_DISPONIVEL,
                                            PROCESSOS_MATERIAIS.QUANTIDADE
                                        FROM COPLAS.PROCESSOS,
                                            COPLAS.PROCESSOS_MATERIAIS,
                                            COPLAS.PRODUTOS,
                                            COPLAS.PRODUTOS MATERIAIS
                                        WHERE PROCESSOS.CHAVE = PROCESSOS_MATERIAIS.CHAVE_PROCESSO
                                            AND PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD
                                            AND PROCESSOS_MATERIAIS.CHAVE_MATERIAL = MATERIAIS.CPROD
                                            AND PROCESSOS.FORA_LINHA = 'NAO'
                                            AND MATERIAIS.CHAVE_FAMILIA = :chave_familia_produto
                                            AND PRODUTOS.CODIGO NOT LIKE '%AMOSTRA%'
                                            AND PRODUTOS.CODIGO NOT LIKE 'ZKIT%'
                                            AND PRODUTOS.CODIGO NOT LIKE 'KIT%'
                                    ) PRODUTOS
                            ) PERIODO,
                            (
                                SELECT EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) || '-' || EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO) AS MES_ANO,
                                    PRODUTOS.CODIGO,
                                    SUM(NOTAS_ITENS.QUANTIDADE * PRODUTOS.QUANTIDADE) AS QUANTIDADE
                                FROM (
                                        SELECT DISTINCT PRODUTOS.CPROD,
                                            MATERIAIS.CODIGO,
                                            PROCESSOS_MATERIAIS.QUANTIDADE
                                        FROM COPLAS.PROCESSOS,
                                            COPLAS.PROCESSOS_MATERIAIS,
                                            COPLAS.PRODUTOS,
                                            COPLAS.PRODUTOS MATERIAIS
                                        WHERE PROCESSOS.CHAVE = PROCESSOS_MATERIAIS.CHAVE_PROCESSO
                                            AND PROCESSOS.CHAVE_PRODUTO = PRODUTOS.CPROD
                                            AND PROCESSOS_MATERIAIS.CHAVE_MATERIAL = MATERIAIS.CPROD
                                            AND PROCESSOS.FORA_LINHA = 'NAO'
                                            AND MATERIAIS.CHAVE_FAMILIA = :chave_familia_produto
                                            AND PRODUTOS.CODIGO NOT LIKE '%AMOSTRA%'
                                            AND PRODUTOS.CODIGO NOT LIKE 'ZKIT%'
                                            AND PRODUTOS.CODIGO NOT LIKE 'KIT%'
                                    ) PRODUTOS,
                                    COPLAS.NOTAS,
                                    COPLAS.NOTAS_ITENS
                                WHERE NOTAS.CHAVE = NOTAS_ITENS.CHAVE_NOTA
                                    AND NOTAS_ITENS.CHAVE_PRODUTO = PRODUTOS.CPROD
                                    AND NOTAS.VALOR_COMERCIAL = 'SIM'
                                    AND NOTAS.ESPECIE = 'S'
                                    AND NOTAS.DATA_EMISSAO >= TRUNC(SYSDATE, 'MM') - INTERVAL '12' MONTH
                                    AND NOTAS.DATA_EMISSAO <= LAST_DAY(TRUNC(SYSDATE, 'MM') - INTERVAL '1' MONTH)
                                GROUP BY PRODUTOS.CODIGO,
                                    EXTRACT(MONTH FROM NOTAS.DATA_EMISSAO) || '-' || EXTRACT(YEAR FROM NOTAS.DATA_EMISSAO)
                            ) MED
                        WHERE PERIODO.CODIGO = MED.CODIGO(+)
                        GROUP BY PERIODO.CPROD,
                            PERIODO.ABC,
                            PERIODO.ESTRATEGICO,
                            PERIODO.CODIGO,
                            PERIODO.ESTOQUE_DISPONIVEL
                    )
            ) PP_MP_PROCESSO
        WHERE CODIGO = PP_MP_CODIGO(+)
        {order_by}
    """

    sql = sql.format(filtro_op=filtro_op, order_by=order_by)

    resultado = executar_oracle(sql, exportar_cabecalho=True, chave_familia_produto=chave_familia_produto)

    if not resultado:
        return []

    return resultado
