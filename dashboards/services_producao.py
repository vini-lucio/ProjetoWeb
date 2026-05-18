from analysis.models import PRODUTOS, OC_MP_ITENS
from django.db.models import Sum, F
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
        self.toneladas_estoque_atual_abc = list(PRODUTOS.coluna_estoque_abc().filter(CHAVE_FAMILIA__pk=7766).values(
            'ESTOQUE_ABC').annotate(
            TONELADAS_ESTOQUE_DISPONIVEL=Sum(F('ESTOQUE_DISPONIVEL') * F('PESO_LIQUIDO') / 1000)).order_by(
                'ESTOQUE_ABC'))
        self.toneladas_estoque_atual_total = 0
        for tonelada_abc in self.toneladas_estoque_atual_abc:  # type:ignore
            self.toneladas_estoque_atual_total += tonelada_abc['TONELADAS_ESTOQUE_DISPONIVEL'] if tonelada_abc['ESTOQUE_ABC'] else 0
            if not tonelada_abc['ESTOQUE_ABC']:
                self.toneladas_estoque_atual_abc.remove(tonelada_abc)  # type:ignore

        # Geração de graficos de toneladas estoque_atual
        dados_grafico_toneladas_estoque_atual_abc = pd.DataFrame(self.toneladas_estoque_atual_abc)
        if not dados_grafico_toneladas_estoque_atual_abc.empty:
            self.grafico_toneladas_estoque_atual_abc_html = self.gerar_graficos_toneladas_abc_html(
                'Estoque', 'TONELADAS_ESTOQUE_DISPONIVEL', 'ESTOQUE_ABC', dados_grafico_toneladas_estoque_atual_abc
            )

        # Detalhe estoque materia prima
        toneladas_estoque_atual_total_materia_prima = list(PRODUTOS.objects.filter(
            CHAVE_GRUPO__pk=8273, ESTOQUE_ATUAL__gt=0).values(PRODUTO=F('CODIGO')).annotate(
            TONELADAS_ESTOQUE_TOTAL=Sum(F('ESTOQUE_ATUAL') * F('PESO_LIQUIDO') / 1000)).order_by('PRODUTO'))

        dt_materia_prima = pd.DataFrame(toneladas_estoque_atual_total_materia_prima)
        dt_materia_prima['TONELADAS_ESTOQUE_TOTAL'] = pd.to_numeric(
            dt_materia_prima['TONELADAS_ESTOQUE_TOTAL'], errors='coerce',
        )

        toneladas_estoque_atual_total_materia_prima_real = []
        mps = PRODUTOS.objects.filter(CHAVE_GRUPO__CHAVE=8273)
        for mp in mps:
            produto = mp.get_produto()
            if produto:
                estoque_real = produto.estoque_total  # type:ignore
                if estoque_real:
                    toneladas_estoque_atual_total_materia_prima_real.append(
                        {'PRODUTO': produto.nome,   # type:ignore
                         'TONELADAS_ESTOQUE_TOTAL_REAL': float(estoque_real) / 1000}
                    )
        dt_materia_prima_real = pd.DataFrame(toneladas_estoque_atual_total_materia_prima_real)

        dt_materia_prima = pd.merge(dt_materia_prima, dt_materia_prima_real,
                                    'outer', 'PRODUTO').fillna(0).sort_values('PRODUTO')

        dt_materia_prima_totais = pd.DataFrame([dt_materia_prima.sum(numeric_only=True)])

        self.toneladas_estoque_atual_total_materia_prima = dt_materia_prima.to_dict(orient='records')
        self.toneladas_estoque_atual_total_materia_prima_totais = dt_materia_prima_totais.to_dict(
            orient='records')[0]

        # Entregas de em aberto
        self.entregas_em_aberto = OC_MP_ITENS.objects.filter(SALDO__gt=0, CHAVE_MATERIAL__CHAVE_GRUPO__pk=8273).values(
            'VALOR_UNITARIO', 'SALDO', 'DATA_ENTREGA', OC=F('CHAVE_OC'),
            FORNECEDOR=F('CHAVE_OC__CHAVE_FORNECEDOR__NOMERED'), PRODUTO=F('CHAVE_MATERIAL__CODIGO'),
            UNIDADE=F('CHAVE_MATERIAL__CHAVE_UNIDADE__UNIDADE'),
        ).order_by('DATA_ENTREGA')

        # Ordens de produção em aberto
        self.ordens_producao_em_aberto = get_relatorios_producao(
            coluna_maquina=True, coluna_chave_ordem_producao=True, coluna_produto=True, coluna_estoque_abc=True,
            status_ordem_producao_em_aberto=True, coluna_cavidades=True, coluna_ciclo_padrao=True, coluna_ciclo=True,
            job=22, setor=3, familia_produto=7766, ordenar_maquina_prioritario=True,
        )

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
        'coluna_maquina': {'maquina_campo_alias': "MAQUINAS.CODIGO AS MAQUINA,",
                           'maquina_campo': "MAQUINAS.CODIGO,", },
        'ordenar_maquina_prioritario': {'maquina_campo': "MAQUINAS.CODIGO,",
                                        'ordenar_maquina_prioritario': "MAQUINAS.CODIGO,", },

        'coluna_chave_ordem_producao': {'chave_ordem_producao_campo_alias': "ORDENS.CHAVE AS OP,",
                                        'chave_ordem_producao_campo': "ORDENS.CHAVE,", },

        'coluna_cavidades_padrao': {'cavidades_padrao_campo_alias': "PROCESSOS_OPERACOES.CAVIDADES AS CAVIDADES_PADRAO,",
                                    'cavidades_padrao_campo': "PROCESSOS_OPERACOES.CAVIDADES,", },

        'coluna_cavidades': {'cavidades_campo_alias': "COALESCE(APONTAMENTOS.CAVIDADES, PROCESSOS_OPERACOES.CAVIDADES) AS CAVIDADES,",
                             'cavidades_campo': "COALESCE(APONTAMENTOS.CAVIDADES, PROCESSOS_OPERACOES.CAVIDADES),", },

        'coluna_ciclo_padrao': {'ciclo_padrao_campo_alias': "PROCESSOS_OPERACOES.CICLO / CASE WHEN PRODUTOS.CHAVE_UNIDADE = 5988 THEN 1000 ELSE 1 END AS CICLO_PADRAO,",
                                'ciclo_padrao_campo': "PROCESSOS_OPERACOES.CICLO, PRODUTOS.CHAVE_UNIDADE,", },

        'coluna_ciclo': {'ciclo_campo_alias': "(SUM(APONTAMENTOS.TEMPO) * 60 / SUM(APONTAMENTOS.PRODUCAO_LIQUIDA) * COALESCE(APONTAMENTOS.CAVIDADES, PROCESSOS_OPERACOES.CAVIDADES)) / CASE WHEN PRODUTOS.CHAVE_UNIDADE = 5988 THEN 1000 ELSE 1 END AS CICLO,",
                         'ciclo_campo': "COALESCE(APONTAMENTOS.CAVIDADES, PROCESSOS_OPERACOES.CAVIDADES), PRODUTOS.CHAVE_UNIDADE,", },

        'status_ordem_producao_em_aberto': {'status_ordem_producao_em_aberto_pesquisa': "ORDENS.STATUS NOT IN ('FECHADA', 'CANCELADA') AND", },

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
            {maquina_campo_alias}
            {chave_ordem_producao_campo_alias}
            {estoque_abc_campo_alias}
            {grupo_produto_campo_alias}
            {produto_campo_alias}
            {unidade_campo_alias}
            {cavidades_padrao_campo_alias}
            {cavidades_campo_alias}
            {ciclo_padrao_campo_alias}
            {ciclo_campo_alias}
            {toneladas_apontadas_liquidas_campo_alias}

            SUM(APONTAMENTOS.TEMPO / 60) AS HORAS_APONTADAS

        FROM
            {grupo_produto_from}

            COPLAS.ORDENS,
            COPLAS.APONTAMENTOS,
            COPLAS.PRODUTOS,
            COPLAS.UNIDADES,
            COPLAS.PROCESSOS,
            COPLAS.PROCESSOS_OPERACOES,
            COPLAS.MAQUINAS,
            COPLAS.JOBS

        WHERE
            {grupo_produto_join}

            ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM AND
            ORDENS.CHAVE_PRODUTO = PRODUTOS.CPROD AND
            PRODUTOS.CHAVE_UNIDADE = UNIDADES.CHAVE AND
            ORDENS.CHAVE_JOB = JOBS.CODIGO AND
            ORDENS.CHAVE_PROCESSO = PROCESSOS.CHAVE AND
            PROCESSOS.CHAVE = PROCESSOS_OPERACOES.CHAVE_PROCESSO AND
            APONTAMENTOS.CHAVE_SETOR = PROCESSOS_OPERACOES.CHAVE_SETOR AND
            APONTAMENTOS.CHAVE_MAQUINA = MAQUINAS.CHAVE AND

            {estoque_abc_pesquisa}
            {grupo_produto_pesquisa}
            {produto_pesquisa}
            {produto_marca_pesquisa}
            {job_pesquisa}
            {data_apontamento_inicio_maior_igual_pesquisa}
            {data_apontamento_inicio_menor_igual_pesquisa}
            {setor_pesquisa}
            {familia_produto_pesquisa}
            {status_ordem_producao_em_aberto_pesquisa}

            1 = 1

        GROUP BY
            {estoque_abc_campo}
            {grupo_produto_campo}
            {produto_campo}
            {unidade_campo}
            {job_campo}
            {maquina_campo}
            {chave_ordem_producao_campo}
            {cavidades_padrao_campo}
            {cavidades_campo}
            {ciclo_padrao_campo}
            {ciclo_campo}

            1

        ORDER BY
            {ordenar_maquina_prioritario}

            {job_campo}
            {estoque_abc_campo}
            {grupo_produto_campo}
            {produto_campo}

            HORAS_APONTADAS DESC
    """

    sql = sql_base.format_map(DefaultDict(kwargs_sql))
    resultado = executar_oracle(sql, exportar_cabecalho=True, **kwargs_ora)

    return resultado
