from analysis.models import PRODUTOS
from utils.custom import DefaultDict
from utils.oracle.conectar import executar_oracle
from .services import get_relatorios_vendas
from utils.plotly_parametros import update_layout_kwargs
import pandas as pd
import plotly.express as px
import plotly.io as pio


class DashBoardProducao():
    """Gera dashboards de produção."""

    def __init__(self, data_inicio, data_fim) -> None:
        """
        Parametros:
        -----------
        :data_inicio [Date]: com a data inicial do periodo
        :data_fim [Date]: com a data final do periodo
        """
        # Toneladas Transformadas
        self.toneladas_transformadas_abc = get_relatorios_producao(
            data_apontamento_inicio_maior_igual=data_inicio, data_apontamento_inicio_menor_igual=data_fim,
            coluna_estoque_abc=True, coluna_toneladas_apontadas_liquidas=True, job=22, setor=12, familia_produto=7766,
        )
        self.toneladas_transformadas_total = 0
        for tonelada_abc in self.toneladas_transformadas_abc:
            self.toneladas_transformadas_total += tonelada_abc['TONELADAS_APONTADAS_LIQUIDAS'] if tonelada_abc['ESTOQUE_ABC'] else 0
            if not tonelada_abc['ESTOQUE_ABC']:
                self.toneladas_transformadas_abc.remove(tonelada_abc)

        # Geração de graficos de toneladas transformadas
        dados_grafico_toneladas_transformadas_abc = pd.DataFrame(self.toneladas_transformadas_abc)
        if not dados_grafico_toneladas_transformadas_abc.empty:
            self.grafico_toneladas_transformadas_abc_html = self.gerar_graficos_toneladas_abc_html(
                'Transformado', 'TONELADAS_APONTADAS_LIQUIDAS', 'ESTOQUE_ABC', dados_grafico_toneladas_transformadas_abc
            )

        # Toneladas Faturadas
        self.toneladas_faturadas_abc = get_relatorios_vendas(
            fonte='faturamentos', inicio=data_inicio, fim=data_fim,
            coluna_estoque_abc=True, coluna_toneladas_liquidas_produto_documento=True, familia_produto=7766,
            cfop_baixa_estoque=True, incluir_sem_valor_comercial=True,
        )
        self.toneladas_faturadas_total = 0
        for tonelada_abc in self.toneladas_faturadas_abc:
            self.toneladas_faturadas_total += tonelada_abc['TONELADAS_LIQUIDAS_PRODUTO_DOCUMENTO'] if tonelada_abc['ESTOQUE_ABC'] else 0
            if not tonelada_abc['ESTOQUE_ABC']:
                self.toneladas_faturadas_abc.remove(tonelada_abc)

        # Geração de graficos de toneladas faturadas
        dados_grafico_toneladas_faturadas_abc = pd.DataFrame(self.toneladas_faturadas_abc)
        if not dados_grafico_toneladas_faturadas_abc.empty:
            self.grafico_toneladas_faturadas_abc_html = self.gerar_graficos_toneladas_abc_html(
                'Faturado', 'TONELADAS_LIQUIDAS_PRODUTO_DOCUMENTO', 'ESTOQUE_ABC', dados_grafico_toneladas_faturadas_abc
            )

        # Toneladas Estoque Atual
        estoque_atual_abc = toneladas_estoque_disponivel_abc()
        self.toneladas_estoque_atual_abc = estoque_atual_abc[0] if estoque_atual_abc else {}
        self.toneladas_estoque_atual_total = 0
        for tonelada_abc in self.toneladas_estoque_atual_abc.values():
            self.toneladas_estoque_atual_total += tonelada_abc if tonelada_abc else 0

        # Geração de graficos de toneladas estoque_atual
        dados_grafico_toneladas_estoque_atual_abc = pd.DataFrame(estoque_atual_abc)
        if not dados_grafico_toneladas_estoque_atual_abc.empty:
            self.grafico_toneladas_estoque_atual_abc_html = self.gerar_graficos_toneladas_abc_html(
                'Estoque', [ea_valor for ea_chave, ea_valor in self.toneladas_estoque_atual_abc.items()],
                [ea_chave for ea_chave, ea_valor in self.toneladas_estoque_atual_abc.items()],
            )

        # Detalhe estoque materia prima
        toneladas_estoque_atual_disponivel_materia_prima = toneladas_estoque_disponivel_materia_prima()
        dt_materia_prima = pd.DataFrame(toneladas_estoque_atual_disponivel_materia_prima)

        toneladas_estoque_atual_disponivel_materia_prima_real = []
        mps = PRODUTOS.objects.filter(CHAVE_GRUPO__CHAVE=8273)
        for mp in mps:
            produto = mp.get_produto()
            if produto:
                estoque_real = produto.estoque_disponivel_real  # type:ignore
                if estoque_real:
                    toneladas_estoque_atual_disponivel_materia_prima_real.append(
                        {'PRODUTO': produto.nome,   # type:ignore
                         'TONELADAS_ESTOQUE_DISPONIVEL_REAL': float(estoque_real) / 1000}
                    )
        dt_materia_prima_real = pd.DataFrame(toneladas_estoque_atual_disponivel_materia_prima_real)

        dt_materia_prima = pd.merge(dt_materia_prima, dt_materia_prima_real,
                                    'outer', 'PRODUTO').fillna(0).sort_values('PRODUTO')

        dt_materia_prima_totais = pd.DataFrame([dt_materia_prima.sum(numeric_only=True)])

        self.toneladas_estoque_atual_disponivel_materia_prima = dt_materia_prima.to_dict(orient='records')
        self.toneladas_estoque_atual_disponivel_materia_prima_totais = dt_materia_prima_totais.to_dict(
            orient='records')[0]

        # Entregas de em aberto
        self.entregas_em_aberto = entregas_materia_prima_em_aberto()

        # Ordens de produção em aberto
        self.ordens_producao_em_aberto = produtividade_ordens_producao_em_aberto()

    def gerar_graficos_toneladas_abc_html(self, px_pie_title: str, px_pie_values, px_pie_names, px_pie_data_frame=None):
        """Gera html para renderizar graficos.

        Parametros:
        -----------
        :px_pie_title (str): com o titulo do grafico.
        :px_pie_values: com os valores do grafico de pizza no formato que o plotly express aceita.
        :px_pie_names: com os cabeçalhos do grafico de pizza no formato que o plotly express aceita.
        :px_pie_data_frame (opcional, Default None): com o dataframe com os dados do grafico de pizza no formato que o plotly express aceita.

        Retorno:
        --------
        :str: com o html para renderizar o grafico."""
        grafico = px.pie(px_pie_data_frame, title=px_pie_title, values=px_pie_values, names=px_pie_names,)
        grafico.update_layout(update_layout_kwargs, paper_bgcolor='rgb(238, 238, 238)', showlegend=False, height=300,
                              width=300,)
        grafico.update_traces(textinfo='percent+label',)
        return pio.to_html(grafico, full_html=False)


def toneladas_estoque_disponivel_abc() -> list | None:
    """Retorna as toneladas no estoque disponivel de produtos proprios abc.

    Retorno:
    --------
    :list[dict]: com as toneladas no estoque disponivel de produtos proprios abc."""
    sql = """
        SELECT SUM(
                CASE
                    WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN PRODUTOS.ESTOQUE_DISPONIVEL * PRODUTOS.PESO_LIQUIDO
                    ELSE 0
                END
            ) / 1000 AS "A",
            SUM(
                CASE
                    WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN PRODUTOS.ESTOQUE_DISPONIVEL * PRODUTOS.PESO_LIQUIDO
                    ELSE 0
                END
            ) / 1000 AS "B",
            SUM(
                CASE
                    WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN PRODUTOS.ESTOQUE_DISPONIVEL * PRODUTOS.PESO_LIQUIDO
                    ELSE 0
                END
            ) / 1000 AS "C"
        FROM COPLAS.PRODUTOS
        WHERE PRODUTOS.CHAVE_FAMILIA = 7766
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True,)

    if not resultado:
        return []

    return resultado


def toneladas_estoque_reservado_abc() -> list | None:
    """Retorna as toneladas no estoque reservado de produtos proprios abc.

    Retorno:
    --------
    :list[dict]: com as toneladas no estoque reservado de produtos proprios abc."""
    sql = """
        SELECT SUM(
                CASE
                    WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE _%' THEN PRODUTOS.ESTOQUE_RESERVADO * PRODUTOS.PESO_LIQUIDO
                    ELSE 0
                END
            ) / 1000 AS RESERVADO
        FROM COPLAS.PRODUTOS
        WHERE PRODUTOS.CHAVE_FAMILIA = 7766
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True,)

    if not resultado:
        return []

    return resultado


def toneladas_estoque_disponivel_materia_prima() -> list | None:
    """Retorna as toneladas no estoque disponivel de materias primas.

    Retorno:
    --------
    :list[dict]: com as toneladas no estoque disponivel de materias primas."""
    sql = """
        SELECT PRODUTOS.CODIGO AS PRODUTO,
            SUM(
                PRODUTOS.ESTOQUE_DISPONIVEL * PRODUTOS.PESO_LIQUIDO
            ) / 1000 AS TONELADAS_ESTOQUE_DISPONIVEL
        FROM COPLAS.PRODUTOS
        WHERE PRODUTOS.CHAVE_GRUPO = 8273
            AND PRODUTOS.ESTOQUE_ATUAL != 0
        GROUP BY PRODUTOS.CODIGO
        ORDER BY PRODUTOS.CODIGO
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True,)

    if not resultado:
        return []

    return resultado


def entregas_materia_prima_em_aberto() -> list | None:
    """Retorna as entregas de materias primas de ordens de compra em aberto.

    Retorno:
    --------
    :list[dict]: com as entregas de materias primas."""
    sql = """
        SELECT OC_MP_ITENS.CHAVE_OC AS OC,
            FORNECEDORES.NOMERED AS FORNECEDOR,
            PRODUTOS.CODIGO AS PRODUTO,
            OC_MP_ITENS.VALOR_UNITARIO,
            OC_MP_ITENS.SALDO,
            UNIDADES.UNIDADE,
            OC_MP_ITENS.DATA_ENTREGA
        FROM COPLAS.FORNECEDORES,
            COPLAS.UNIDADES,
            COPLAS.OC_MP_ITENS,
            COPLAS.PRODUTOS,
            COPLAS.OC_MP
        WHERE OC_MP.CHAVE = OC_MP_ITENS.CHAVE_OC
            AND FORNECEDORES.CODFOR = OC_MP.CHAVE_FORNECEDOR
            AND UNIDADES.CHAVE = PRODUTOS.CHAVE_UNIDADE
            AND OC_MP_ITENS.CHAVE_MATERIAL = PRODUTOS.CPROD
            AND PRODUTOS.CHAVE_GRUPO = 8273
            AND OC_MP_ITENS.SALDO > 0
        ORDER BY OC_MP_ITENS.DATA_ENTREGA
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True,)

    if not resultado:
        return []

    return resultado


def produtividade_ordens_producao_em_aberto() -> list | None:
    """Retorna as ordens de produção em aberto com o ciclo atual.

    Retorno:
    --------
    :list[dict]: com as ordens de produção em aberto."""
    sql = """
        SELECT MAQUINAS.CODIGO AS MAQUINA,
            ORDENS.CHAVE AS OP,
            PRODUTOS.CODIGO AS PRODUTO,
            CASE
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A'
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B'
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C'
                ELSE NULL
            END AS ABC,
            COALESCE(
                APONTAMENTOS.CAVIDADES,
                PROCESSOS_OPERACOES.CAVIDADES
            ) AS CAVIDADES,
            CASE
                WHEN PRODUTOS.CHAVE_UNIDADE = 5988 THEN PROCESSOS_OPERACOES.CICLO / 1000
                ELSE PROCESSOS_OPERACOES.CICLO
            END AS CICLO_PADRAO,
            CASE
                WHEN PRODUTOS.CHAVE_UNIDADE = 5988 THEN SUM(APONTAMENTOS.TEMPO) * 60 / SUM(APONTAMENTOS.PRODUCAO_LIQUIDA) * COALESCE(
                    APONTAMENTOS.CAVIDADES,
                    PROCESSOS_OPERACOES.CAVIDADES
                ) / 1000
                ELSE SUM(APONTAMENTOS.TEMPO) * 60 / SUM(APONTAMENTOS.PRODUCAO_LIQUIDA) * COALESCE(
                    APONTAMENTOS.CAVIDADES,
                    PROCESSOS_OPERACOES.CAVIDADES
                )
            END AS CICLO_ATUAL
        FROM COPLAS.ORDENS,
            COPLAS.PRODUTOS,
            COPLAS.PROCESSOS,
            COPLAS.PROCESSOS_OPERACOES,
            COPLAS.APONTAMENTOS,
            COPLAS.MAQUINAS
        WHERE ORDENS.CHAVE_PRODUTO = PRODUTOS.CPROD
            AND ORDENS.CHAVE_PROCESSO = PROCESSOS.CHAVE
            AND PROCESSOS.CHAVE = PROCESSOS_OPERACOES.CHAVE_PROCESSO
            AND ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM(+)
            AND APONTAMENTOS.CHAVE_MAQUINA = MAQUINAS.CHAVE(+)
            AND PROCESSOS_OPERACOES.CHAVE_SETOR = 3
            AND (
                APONTAMENTOS.CHAVE_SETOR = 3
                OR APONTAMENTOS.CHAVE_SETOR IS NULL
            )
            AND PRODUTOS.CHAVE_FAMILIA = 7766
            AND ORDENS.STATUS NOT IN ('FECHADA', 'CANCELADA')
            AND APONTAMENTOS.CHAVE_MAQUINA IS NOT NULL
        GROUP BY MAQUINAS.CODIGO,
            ORDENS.CHAVE,
            PRODUTOS.CODIGO,
            CASE
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A'
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B'
                WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C'
                ELSE NULL
            END,
            COALESCE(
                APONTAMENTOS.CAVIDADES,
                PROCESSOS_OPERACOES.CAVIDADES
            ),
            PRODUTOS.CHAVE_UNIDADE,
            PROCESSOS_OPERACOES.CICLO
        ORDER BY MAQUINAS.CODIGO,
            ABC,
            PRODUTOS.CODIGO
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True,)

    if not resultado:
        return []

    return resultado


def map_relatorio_producao_sql_string_placeholders(**kwargs_formulario):
    """Retorna codigos SQL para placeholders da função get_relatorios_producao.

    Parametros:
    -----------
    :kwargs_formulario [dict]: com os campos para serem exibidos (sempre começam com 'coluna') ou filtrados. Exemplos:

    >>> {'coluna_campo_x': True, 'campo_x': '%%teste%%'}

    Retorno:
    --------
    :dict: com placeholders do SQL na chave e o valor com o codigo SQL (dentro do SQL pode haver placeholders do banco de dados)."""

    # Apontamentos colunas e filtros
    """
        Exemplo nomenclatura colunas:
        'coluna_x': {
            'x_campo_alias': "TESTE AS TESTE,", # campo do select (obrigatorio)
            'x_campo': "X,",                    # campo do group by (opcional se for campo agregado) ou order by (opcional)
            'x_from': "TABELA,",                # tabela do from (obrigatorio se coluna for de uma tabela que não está no padrão)
            'x_join': "TESTE = TESTE AND",      # join no where (obrigatorio se coluna for de uma tabela que não está no padrão)
        }

        Exemplo nomenclatura filtros:
        'x': {
            'x_pesquisa': "TESTE = TESTE AND", # condição do where (obrigatorio)
            'x_from': "TABELA,",               # tabela do from (obrigatorio se coluna for de uma tabela que não está no padrão)
            'x_join': "TESTE = TESTE AND",     # join no where (obrigatorio se coluna for de uma tabela que não está no padrão)
        }
    """
    map_sql_apontamentos = {
        'coluna_estoque_abc': {'estoque_abc_campo_alias': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END AS ESTOQUE_ABC,",
                               'estoque_abc_campo': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END,", },
        'estoque_abc': {'estoque_abc_pesquisa': "CASE WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE A%' THEN 'A' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE B%' THEN 'B' WHEN PRODUTOS.CARACTERISTICA2 LIKE '%ESTOQUE C%' THEN 'C' END = UPPER(:estoque_abc) AND", },

        'coluna_grupo_produto': {'grupo_produto_campo_alias': "GRUPO_PRODUTOS.GRUPO AS GRUPO_PRODUTO,",
                                 'grupo_produto_campo': "GRUPO_PRODUTOS.GRUPO,",
                                 'grupo_produto_from': "COPLAS.GRUPO_PRODUTOS,",
                                 'grupo_produto_join': "PRODUTOS.CHAVE_GRUPO = GRUPO_PRODUTOS.CHAVE AND", },
        'grupo_produto': {'grupo_produto_pesquisa': "GRUPO_PRODUTOS.CHAVE = :chave_grupo_produto AND",
                          'grupo_produto_from': "COPLAS.GRUPO_PRODUTOS,",
                          'grupo_produto_join': "PRODUTOS.CHAVE_GRUPO = GRUPO_PRODUTOS.CHAVE AND", },

        'coluna_produto': {'produto_campo_alias': "PRODUTOS.CODIGO AS PRODUTO,",
                           'produto_campo': "PRODUTOS.CODIGO,", },
        'produto': {'produto_pesquisa': "UPPER(PRODUTOS.CODIGO) LIKE UPPER(:produto) AND", },
        'produto_marca': {'produto_marca_pesquisa': "PRODUTOS.CHAVE_MARCA = :chave_produto_marca AND", },

        'coluna_unidade': {'unidade_campo_alias': "UNIDADES.UNIDADE,",
                           'unidade_campo': "UNIDADES.UNIDADE,", },

        'coluna_job': {'job_campo_alias': "JOBS.DESCRICAO AS JOB,",
                       'job_campo': "JOBS.DESCRICAO,", },
        'job': {'job_pesquisa': "JOBS.CODIGO = :chave_job AND", },

        'data_apontamento_inicio_maior_igual': {'data_apontamento_inicio_maior_igual_pesquisa': "TRUNC(APONTAMENTOS.INICIO) >= :data_apontamento_inicio_maior_igual AND", },
        'data_apontamento_inicio_menor_igual': {'data_apontamento_inicio_menor_igual_pesquisa': "TRUNC(APONTAMENTOS.INICIO) <= :data_apontamento_inicio_menor_igual AND", },

        'coluna_toneladas_apontadas_liquidas': {'toneladas_apontadas_liquidas_campo_alias': "SUM(APONTAMENTOS.PRODUCAO_LIQUIDA * PRODUTOS.PESO_LIQUIDO / 1000) AS TONELADAS_APONTADAS_LIQUIDAS,", },

        'setor': {'setor_pesquisa': "APONTAMENTOS.CHAVE_SETOR = :chave_setor AND", },

        'familia_produto': {'familia_produto_pesquisa': "PRODUTOS.CHAVE_FAMILIA = :chave_familia_produto AND", }
    }

    sql_final = {}
    for chave, valor in kwargs_formulario.items():
        if valor:
            get_map_apontamentos = map_sql_apontamentos.get(chave)
            if get_map_apontamentos:
                sql_final.update(get_map_apontamentos)  # type:ignore

    return sql_final


def get_relatorios_producao(**kwargs):
    """Retorna relatorio de produção personalizavel (também funciona com formularios).

    Parametros:
    -----------
    :kwargs [dict]: com os campos para serem exibidos (sempre começam com 'coluna') ou filtrados. Exemplos:

    >>> {'coluna_campo_x': True, 'campo_x': '%%teste%%'}

    Retorno:
    --------
    :list[dict]: com o relatorio."""
    kwargs_sql = {}
    kwargs_ora = {}

    # Campos com filtro
    codigo_sql = kwargs.get('codigo_sql')
    data_apontamento_inicio_maior_igual = kwargs.get('data_apontamento_inicio_maior_igual')
    data_apontamento_inicio_menor_igual = kwargs.get('data_apontamento_inicio_menor_igual')
    estoque_abc = kwargs.get('estoque_abc')
    grupo_produto = kwargs.get('grupo_produto')
    produto = kwargs.get('produto')
    produto_marca = kwargs.get('produto_marca')
    job = kwargs.get('job')
    setor = kwargs.get('setor')
    familia_produto = kwargs.get('familia_produto')

    kwargs_sql.update(map_relatorio_producao_sql_string_placeholders(**kwargs))

    # kwargs_ora precisa conter os placeholders corretamente

    if codigo_sql:
        kwargs_ora.update({'codigo_sql': codigo_sql, })

    if data_apontamento_inicio_maior_igual:
        kwargs_ora.update({'data_apontamento_inicio_maior_igual': data_apontamento_inicio_maior_igual})

    if data_apontamento_inicio_menor_igual:
        kwargs_ora.update({'data_apontamento_inicio_menor_igual': data_apontamento_inicio_menor_igual})

    if grupo_produto:
        chave_grupo_produto = grupo_produto if isinstance(grupo_produto, int) else grupo_produto.pk
        kwargs_ora.update({'chave_grupo_produto': chave_grupo_produto, })

    if produto:
        kwargs_ora.update({'produto': produto, })

    if produto_marca:
        chave_produto_marca = produto_marca if isinstance(produto_marca, int) else produto_marca.pk
        kwargs_ora.update({'chave_produto_marca': chave_produto_marca, })

    if job:
        chave_job = job if isinstance(job, int) else job.pk
        kwargs_ora.update({'chave_job': chave_job, })

    if estoque_abc:
        kwargs_ora.update({'estoque_abc': estoque_abc})

    if setor:
        chave_setor = setor if isinstance(setor, int) else setor.pk
        kwargs_ora.update({'chave_setor': chave_setor, })

    if familia_produto:
        chave_familia_produto = familia_produto if isinstance(familia_produto, int) else familia_produto.pk
        kwargs_ora.update({'chave_familia_produto': chave_familia_produto, })

    sql_base = """
        SELECT
            {job_campo_alias}
            {estoque_abc_campo_alias}
            {grupo_produto_campo_alias}
            {produto_campo_alias}
            {unidade_campo_alias}
            {toneladas_apontadas_liquidas_campo_alias}

            SUM(APONTAMENTOS.TEMPO / 60) AS HORAS_APONTADAS

        FROM
            {grupo_produto_from}

            COPLAS.ORDENS,
            COPLAS.APONTAMENTOS,
            COPLAS.PRODUTOS,
            COPLAS.UNIDADES,
            COPLAS.JOBS

        WHERE
            {grupo_produto_join}

            ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM AND
            ORDENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
            PRODUTOS.CHAVE_UNIDADE = UNIDADES.CHAVE AND
            ORDENS.CHAVE_JOB = JOBS.CODIGO AND

            {estoque_abc_pesquisa}
            {grupo_produto_pesquisa}
            {produto_pesquisa}
            {produto_marca_pesquisa}
            {job_pesquisa}
            {data_apontamento_inicio_maior_igual_pesquisa}
            {data_apontamento_inicio_menor_igual_pesquisa}
            {setor_pesquisa}
            {familia_produto_pesquisa}

            1 = 1

        GROUP BY
            {estoque_abc_campo}
            {grupo_produto_campo}
            {produto_campo}
            {unidade_campo}
            {job_campo}

            1

        ORDER BY
            {job_campo}
            {estoque_abc_campo}
            {grupo_produto_campo}
            {produto_campo}

            HORAS_APONTADAS DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, **kwargs_ora)

    return resultado
