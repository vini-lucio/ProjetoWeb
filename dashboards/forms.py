from django import forms
from django.forms.widgets import DateInput
from .models import Indicadores
from utils.base_forms import FormPeriodoInicioFimMixIn, FormVendedoresMixIn, FormPesquisarIntegerMixIn
from analysis.models import (VENDEDORES, CLIENTES_TIPOS, FAIXAS_CEP, ESTADOS, FAMILIA_PRODUTOS, STATUS_ORCAMENTOS_ITENS,
                             INFORMACOES_CLI, JOBS, MARCAS, GRUPO_PRODUTOS)
from utils.data_hora_atual import hoje_as_yyyymmdd
from datetime import date, timedelta


class FormAnaliseOrcamentos(FormPesquisarIntegerMixIn, forms.Form):
    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pesquisar'].label = 'n° Orçamento'

        if not usuario or (not usuario.is_superuser and not usuario.groups.filter(name='Supervisão').exists()):
            escolhas = self.fields['desconto'].choices
            self.fields['desconto'].choices = [escolha for escolha in escolhas if escolha[0] != 'desconto_preco_atual']

    descontos = {
        'desconto_preco_tabela': '% Sobre Preço de Tabela',
        'desconto_preco_atual': '% Sobre Preço Atual',
        'margem': '% Margem',
    }

    desconto = forms.ChoiceField(label="Desconto", choices=descontos, initial='desconto_preco_tabela')  # type: ignore
    valor = forms.DecimalField(label="%", initial=0)


class FormDashboardVendasCarteiras(FormVendedoresMixIn, FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()
        self.fields['carteira'].required = False

    fontes = {
        'pedidos': 'Pedidos',
        'orcamentos': 'Orcamentos',
        'faturamentos': 'Faturamentos',
    }

    fonte = forms.ChoiceField(label="Fonte", choices=fontes, initial='pedidos', required=True)  # type: ignore
    em_aberto = forms.BooleanField(label="Em Aberto", help_text="Independente do periodo",
                                   initial=False, required=False)

    def clean_inicio(self):
        inicio = self.cleaned_data['inicio']
        data_minima = date.today() - timedelta(days=365)

        if inicio <= data_minima:
            raise forms.ValidationError("Data de inicio não pode ser antes de um ano atras")

        return inicio


class RelatoriosSupervisaoBaseForm(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()

    carteiras = VENDEDORES.objects.all().order_by('NOMERED')
    representantes = VENDEDORES.objects.all().order_by('NOMERED')
    clientes_tipos = CLIENTES_TIPOS.objects.all().order_by('DESCRICAO')
    cidades = FAIXAS_CEP.objects.all().order_by('CIDADE')
    estados = ESTADOS.objects.all().order_by('ESTADO')
    familias_produtos = FAMILIA_PRODUTOS.objects.all().order_by('FAMILIA')
    grupos_produtos = GRUPO_PRODUTOS.objects.all().order_by('GRUPO')
    informacoes_estrategicas = INFORMACOES_CLI.objects.all().order_by('DESCRICAO')
    jobs = JOBS.objects.all().order_by('DESCRICAO')
    marcas = MARCAS.objects.all().order_by('MARCA')

    # Campos Sobre Cliente
    coluna_grupo_economico = forms.BooleanField(label="Coluna Grupo Economico", initial=True, required=False)
    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)
    cnpj_cpf = forms.CharField(label="CNPJ / CPF", max_length=18, required=False)
    coluna_carteira = forms.BooleanField(label="Coluna Carteira", initial=True, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)
    carteira_parede_de_concreto = forms.BooleanField(label="Carteira Parede de Concreto",
                                                     initial=False, required=False)
    carteira_premoldado_poste = forms.BooleanField(label="Carteira Pré Moldado / Poste",
                                                   initial=False, required=False)
    coluna_tipo_cliente = forms.BooleanField(label="Coluna Tipo", initial=False, required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo", required=False)
    coluna_cidade = forms.BooleanField(label="Coluna Cidade Principal", initial=False, required=False)
    cidade = forms.CharField(label="Cidade Principal", max_length=300, required=False)
    coluna_estado = forms.BooleanField(label="Coluna Estado Principal", initial=False, required=False)
    estado = forms.ModelChoiceField(estados, label="Estado Principal", required=False)
    coluna_segundo_representante = forms.BooleanField(label="Coluna Segundo Representante", initial=False,
                                                      required=False)
    segundo_representante = forms.ModelChoiceField(representantes, label="Segundo Representante", required=False)
    informacao_estrategica = forms.ModelChoiceField(informacoes_estrategicas, label="Informação Estrategica",
                                                    required=False)

    # Campos Sobre Produto
    coluna_familia_produto = forms.BooleanField(label="Coluna Familia", initial=False, required=False)
    familia_produto = forms.ModelChoiceField(familias_produtos, label="Familia", required=False)
    coluna_grupo_produto = forms.BooleanField(label="Coluna Grupo", initial=False, required=False)
    grupo_produto = forms.ModelChoiceField(grupos_produtos, label="Grupo", required=False)
    coluna_produto = forms.BooleanField(label="Coluna Produto", initial=False, required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)
    coluna_unidade = forms.BooleanField(label="Coluna Unidade", initial=False, required=False)
    coluna_preco_tabela_inclusao = forms.BooleanField(label="Coluna Preço de Tabela R$",
                                                      help_text="na inclusão, maior (exceto excluidos)",
                                                      initial=False, required=False)
    coluna_preco_venda_medio = forms.BooleanField(label="Coluna Preço Medio R$", help_text="exceto excluidos",
                                                  initial=False, required=False)
    coluna_quantidade = forms.BooleanField(label="Coluna Quantidade", initial=False, required=False)
    coluna_estoque_abc = forms.BooleanField(label="Coluna Estoque ABC", initial=False, required=False)
    produto_marca = forms.ModelChoiceField(marcas, label="Marca", required=False)

    # Campos Gerais
    codigo_sql = forms.BooleanField(label="Codigo SQL", initial=False, required=False)
    coluna_job = forms.BooleanField(label="Coluna Job", initial=True, required=False)
    job = forms.ModelChoiceField(jobs, label="Job", required=False)
    coluna_rentabilidade = forms.BooleanField(label="Coluna % MC", help_text="exceto excluidos", initial=False,
                                              required=False)
    coluna_rentabilidade_valor = forms.BooleanField(label="Coluna R$ MC", help_text="exceto excluidos", initial=False,
                                                    required=False)
    coluna_quantidade_documentos = forms.BooleanField(label="Coluna Quantidade de Documentos", initial=False,
                                                      required=False)
    coluna_ano_emissao = forms.BooleanField(label="Coluna Ano Emissão", initial=False, required=False)
    coluna_mes_emissao = forms.BooleanField(label="Coluna Mês Emissão", initial=False, required=False)
    coluna_dia_emissao = forms.BooleanField(label="Coluna Dia Emissão", initial=False, required=False)
    coluna_ano_a_ano = forms.BooleanField(label="Colunas Valor Mercadorias Ano a Ano", initial=False, required=False,
                                          help_text="Inicio precisa ser 01/01 e fim 31/12")
    coluna_mes_a_mes = forms.BooleanField(label="Colunas Valor Mercadorias Mês a Mês", initial=False, required=False,
                                          help_text="Inicio precisa ser dia 1 e fim o ultimo dia do mês")
    coluna_media_dia = forms.BooleanField(label="Coluna R$ Médio por Dia", help_text="de venda (exceto excluidos)",
                                          initial=False, required=False)
    coluna_documento = forms.BooleanField(label="Coluna Documento", initial=False, required=False)
    coluna_representante_documento = forms.BooleanField(label="Coluna Representante Documento", initial=False,
                                                        required=False)
    representante_documento = forms.ModelChoiceField(representantes, label="Representante Documento", required=False)
    coluna_log_nome_inclusao_documento = forms.BooleanField(label="Coluna Log Inclusão do Documento", initial=False,
                                                            required=False)

    def get_agrupamentos_campos(self):
        agrupamentos = {
            'Data de Emissao': ['inicio', 'fim',],

            'Sobre Cliente': ['coluna_grupo_economico', 'coluna_carteira', 'coluna_tipo_cliente', 'coluna_cidade',
                              'coluna_estado', 'coluna_segundo_representante', 'grupo_economico', 'carteira',
                              'carteira_parede_de_concreto', 'carteira_premoldado_poste', 'tipo_cliente', 'cidade',
                              'estado', 'informacao_estrategica', 'segundo_representante', 'cnpj_cpf',],

            'Sobre Produto': ['coluna_familia_produto', 'coluna_produto', 'coluna_unidade',
                              'coluna_preco_tabela_inclusao', 'coluna_preco_venda_medio', 'coluna_quantidade',
                              'coluna_estoque_abc', 'familia_produto', 'produto', 'produto_marca',
                              'coluna_grupo_produto', 'grupo_produto',],

            'Geral': ['coluna_job', 'coluna_rentabilidade', 'coluna_rentabilidade_valor',
                      'coluna_quantidade_documentos', 'coluna_ano_emissao', 'coluna_mes_emissao', 'coluna_dia_emissao',
                      'coluna_media_dia', 'coluna_documento', 'coluna_representante_documento', 'coluna_ano_a_ano',
                      'coluna_mes_a_mes', 'job', 'representante_documento', 'coluna_log_nome_inclusao_documento',
                      'codigo_sql',],
        }

        return agrupamentos


class RelatoriosSupervisaoFaturamentosForm(RelatoriosSupervisaoBaseForm):
    # Campos Sobre Cliente
    nao_compraram_depois = forms.BooleanField(label="Não Compraram Depois do Periodo",
                                              help_text="e sem orçamentos em aberto", initial=False, required=False)

    def get_agrupamentos_campos(self):
        super_agrupamento = super().get_agrupamentos_campos()

        super_agrupamento['Sobre Cliente'].append('nao_compraram_depois')

        return super_agrupamento


class RelatoriosSupervisaoOrcamentosForm(RelatoriosSupervisaoBaseForm):
    STATUS = STATUS_ORCAMENTOS_ITENS.objects

    status_orcamentos_itens = STATUS.all().order_by('DESCRICAO')
    status_orcamentos_itens_tipos = list(STATUS.values_list('TIPO', 'TIPO').distinct())
    status_orcamentos_itens_tipos.insert(0, ('', '---------'))
    status_orcamentos_itens_tipos.insert(1, ('PERDIDO_CANCELADO', 'PERDIDO OU CANCELADO'))

    # Campos Sobre Produto
    coluna_status_produto_orcamento = forms.BooleanField(label="Coluna Status", initial=False, required=False)
    status_produto_orcamento = forms.ModelChoiceField(status_orcamentos_itens, label="Status", required=False)
    coluna_status_produto_orcamento_tipo = forms.BooleanField(label="Coluna Status Tipo", initial=False,
                                                              required=False)
    status_produto_orcamento_tipo = forms.ChoiceField(label="Status Tipo", choices=status_orcamentos_itens_tipos,
                                                      initial=False, required=False)
    desconsiderar_justificativas = forms.BooleanField(label="Desconsiderar Justificativas Invalidas",
                                                      help_text="de orçamentos não fechados",
                                                      initial=True, required=False)
    considerar_itens_excluidos = forms.BooleanField(label="Considerar Itens Excluidos",
                                                    help_text="com justificativas validas",
                                                    initial=True, required=False)

    def get_agrupamentos_campos(self):
        super_agrupamento = super().get_agrupamentos_campos()

        super_agrupamento['Sobre Produto'].append('coluna_status_produto_orcamento')
        super_agrupamento['Sobre Produto'].append('coluna_status_produto_orcamento_tipo')
        super_agrupamento['Sobre Produto'].append('status_produto_orcamento')
        super_agrupamento['Sobre Produto'].append('status_produto_orcamento_tipo')
        super_agrupamento['Sobre Produto'].append('desconsiderar_justificativas')
        super_agrupamento['Sobre Produto'].append('considerar_itens_excluidos')

        return super_agrupamento


class FormEventos(FormVendedoresMixIn, forms.Form):
    incluir_futuros = forms.BooleanField(label="Incluir Eventos Futuros", initial=False, required=False)


class FormEventosDesconsiderar(FormVendedoresMixIn, forms.Form):
    desconsiderar_futuros = forms.BooleanField(label="Desconsiderar grupos com eventos futuros", initial=False,
                                               required=False)


class FormIndicadores(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['inicio'].initial = hoje_as_yyyymmdd()
        # self.fields['fim'].initial = hoje_as_yyyymmdd()
        self.fields['inicio'].required = False
        self.fields['fim'].required = False

    indicadores = Indicadores.objects

    valores_tipos = {
        'proporcional': 'Proporcional',
        'real': 'Real',
    }

    frequencias = {
        'mensal': 'Mensal',
        'anual': 'Anual',
    }

    indicador = forms.ModelChoiceField(indicadores, label="Indicador")
    valores = forms.ChoiceField(label="Valores", choices=valores_tipos,  # type: ignore
                                initial='proporcional', required=True)
    frequencia = forms.ChoiceField(label="Frequencia Valores", choices=frequencias,  # type: ignore
                                   initial='mensal', required=True)


class RelatoriosFinanceirosForm(forms.Form):
    jobs = JOBS.objects.all().order_by('DESCRICAO')
    condicoes = [('', '---------'), ('EM ABERTO', 'Em Aberto'), ('LIQUIDADO', 'Liquidado')]

    # Campos Datas
    data_vencimento_inicio = forms.DateField(label="Vencimento Inicio", required=False,
                                             widget=DateInput(attrs={'type': 'date'}))
    data_vencimento_fim = forms.DateField(label="Vencimento Fim", required=False,
                                          widget=DateInput(attrs={'type': 'date'}))
    data_emissao_inicio = forms.DateField(label="Emissão Inicio", required=False,
                                          widget=DateInput(attrs={'type': 'date'}))
    data_emissao_fim = forms.DateField(label="Emissão Fim", required=False, widget=DateInput(attrs={'type': 'date'}))
    data_liquidacao_inicio = forms.DateField(label="Liquidação Inicio", required=False,
                                             widget=DateInput(attrs={'type': 'date'}))
    data_liquidacao_fim = forms.DateField(label="Liquidação Fim", required=False,
                                          widget=DateInput(attrs={'type': 'date'}))

    # Campos Sobre Receber
    coluna_cliente = forms.BooleanField(label="Coluna Cliente", initial=False, required=False)
    cliente = forms.CharField(label="Cliente", help_text="nome reduzido", max_length=300, required=False)
    coluna_carteira = forms.BooleanField(label="Coluna Carteira", initial=False, required=False)
    carteira_parede_de_concreto = forms.BooleanField(label="Carteira Parede de Concreto", initial=False,
                                                     required=False)
    carteira_premoldado_poste = forms.BooleanField(label="Carteira Pré Moldado / Poste", initial=False, required=False)
    carteira_infra = forms.BooleanField(label="Carteira Infra", initial=False, required=False)

    # Campos Sobre Receber
    coluna_fornecedor = forms.BooleanField(label="Coluna Fornecedor", initial=False, required=False)
    fornecedor = forms.CharField(label="Fornecedor", help_text="nome reduzido", max_length=300, required=False)

    # Campos Gerais
    codigo_sql = forms.BooleanField(label="Codigo SQL", initial=False, required=False)
    coluna_job = forms.BooleanField(label="Coluna Job", initial=False, required=False)
    job = forms.ModelChoiceField(jobs, label="Job", required=False)
    coluna_valor_titulo = forms.BooleanField(label="Coluna Valor Titulo", initial=True, required=False)
    coluna_valor_titulo_liquido_desconto = forms.BooleanField(label="Coluna Valor Titulo Liquido de Descontos",
                                                              initial=True, required=False)
    coluna_mes_emissao = forms.BooleanField(label="Coluna Mês Emissão", initial=False, required=False)
    coluna_mes_vencimento = forms.BooleanField(label="Coluna Mês Vencimento", initial=False, required=False)
    coluna_mes_liquidacao = forms.BooleanField(label="Coluna Mês Liquidação", initial=False, required=False)
    coluna_codigo_plano_conta = forms.BooleanField(label="Coluna Codigo Plano de Contas", initial=False,
                                                   required=False)
    coluna_plano_conta = forms.BooleanField(label="Coluna Plano de Contas", initial=False, required=False)
    plano_conta_descricao = forms.CharField(label="Plano de Contas", help_text="codigo ou descrição",
                                            max_length=300, required=False)
    desconsiderar_plano_conta_investimentos = forms.BooleanField(label="Desconsiderar Plano de Contas de Investimentos",
                                                                 initial=True, required=False)
    coluna_condicao = forms.BooleanField(label="Coluna Condição", initial=False, required=False)
    condicao = forms.ChoiceField(label='Condição', choices=condicoes, required=False)

    def get_agrupamentos_campos(self):
        agrupamentos = {
            'Datas': ['data_vencimento_inicio', 'data_vencimento_fim', 'data_emissao_inicio', 'data_emissao_fim',
                      'data_liquidacao_inicio', 'data_liquidacao_fim',],

            'Sobre Receber': ['coluna_cliente', 'cliente', 'coluna_carteira', 'carteira_parede_de_concreto',
                              'carteira_premoldado_poste', 'carteira_infra',],

            'Sobre Pagar': ['coluna_fornecedor', 'fornecedor',],

            'Geral': ['condicao', 'coluna_valor_titulo', 'coluna_job', 'job', 'coluna_mes_emissao',
                      'coluna_mes_vencimento', 'coluna_mes_liquidacao', 'coluna_codigo_plano_conta',
                      'coluna_plano_conta', 'plano_conta_descricao', 'coluna_valor_titulo_liquido_desconto',
                      'desconsiderar_plano_conta_investimentos', 'coluna_condicao', 'codigo_sql',],
        }

        return agrupamentos
