from django import forms
from utils.base_forms import FormPeriodoInicioFimMixIn, FormVendedoresMixIn, FormPesquisarIntegerMixIn
from analysis.models import (VENDEDORES, CLIENTES_TIPOS, FAIXAS_CEP, ESTADOS, FAMILIA_PRODUTOS, STATUS_ORCAMENTOS_ITENS,
                             INFORMACOES_CLI, JOBS)
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

    carteiras = VENDEDORES.objects.filter(CHAVE_CANAL=9).all().order_by('NOMERED')
    clientes_tipos = CLIENTES_TIPOS.objects.all().order_by('DESCRICAO')
    cidades = FAIXAS_CEP.objects.all().order_by('CIDADE')
    estados = ESTADOS.objects.all().order_by('ESTADO')
    familias_produtos = FAMILIA_PRODUTOS.objects.all().order_by('FAMILIA')
    informacoes_estrategicas = INFORMACOES_CLI.objects.all().order_by('DESCRICAO')
    jobs = JOBS.objects.all().order_by('DESCRICAO')

    coluna_job = forms.BooleanField(label="Coluna Job", initial=True, required=False)
    coluna_grupo_economico = forms.BooleanField(label="Coluna Grupo Economico", initial=True, required=False)
    coluna_carteira = forms.BooleanField(label="Coluna Carteira", initial=True, required=False)
    coluna_tipo_cliente = forms.BooleanField(label="Coluna Tipo", initial=False, required=False)
    coluna_cidade = forms.BooleanField(label="Coluna Cidade Principal", initial=False, required=False)
    coluna_estado = forms.BooleanField(label="Coluna Estado Principal", initial=False, required=False)
    coluna_familia_produto = forms.BooleanField(label="Coluna Familia", initial=False, required=False)
    coluna_produto = forms.BooleanField(label="Coluna Produto", initial=False, required=False)
    coluna_unidade = forms.BooleanField(label="Coluna Unidade", initial=False, required=False)
    coluna_preco_tabela_inclusao = forms.BooleanField(label="Coluna Preço de Tabela R$",
                                                      help_text="na inclusão, maior (exceto excluidos)",
                                                      initial=False, required=False)
    coluna_preco_venda_medio = forms.BooleanField(label="Coluna Preço Medio R$", help_text="exceto excluidos",
                                                  initial=False, required=False)
    coluna_quantidade = forms.BooleanField(label="Coluna Quantidade", initial=False, required=False)
    coluna_rentabilidade = forms.BooleanField(label="Coluna % MC", help_text="exceto excluidos", initial=False,
                                              required=False)
    coluna_rentabilidade_valor = forms.BooleanField(label="Coluna R$ MC", help_text="exceto excluidos", initial=False,
                                                    required=False)
    coluna_proporcao = forms.BooleanField(label="Coluna % Proporção", initial=True, required=False)
    coluna_quantidade_documentos = forms.BooleanField(label="Coluna Quantidade de Documentos", initial=False,
                                                      required=False)
    coluna_ano_emissao = forms.BooleanField(label="Coluna Ano Emissão", initial=False, required=False)
    coluna_mes_emissao = forms.BooleanField(label="Coluna Mês Emissão", initial=False, required=False)
    coluna_dia_emissao = forms.BooleanField(label="Coluna Dia Emissão", initial=False, required=False)
    coluna_media_dia = forms.BooleanField(label="Coluna R$ Médio por Dia", help_text="de venda (exceto excluidos)",
                                          initial=False, required=False)
    coluna_documento = forms.BooleanField(label="Coluna Documento", initial=False, required=False)

    job = forms.ModelChoiceField(jobs, label="Job", required=False)
    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)
    carteira_parede_de_concreto = forms.BooleanField(label="Carteira Parede de Concreto",
                                                     initial=False, required=False)
    carteira_premoldado_poste = forms.BooleanField(label="Carteira Pré Moldado / Poste",
                                                   initial=False, required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo", required=False)
    cidade = forms.CharField(label="Cidade Principal", max_length=300, required=False)
    estado = forms.ModelChoiceField(estados, label="Estado Principal", required=False)
    familia_produto = forms.ModelChoiceField(familias_produtos, label="Familia", required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)
    informacao_estrategica = forms.ModelChoiceField(informacoes_estrategicas, label="Informação Estrategica",
                                                    required=False)

    def get_agrupamentos_campos(self):
        agrupamentos = {
            'Data de Emissao': ['inicio', 'fim',],

            'Visualizações sobre Cliente': ['coluna_grupo_economico', 'coluna_carteira', 'coluna_tipo_cliente',
                                            'coluna_cidade', 'coluna_estado',],
            'Visualizações sobre Produto': ['coluna_familia_produto', 'coluna_produto', 'coluna_unidade',
                                            'coluna_preco_tabela_inclusao', 'coluna_preco_venda_medio',
                                            'coluna_quantidade',],
            'Visualizações Gerais': ['coluna_job', 'coluna_rentabilidade', 'coluna_rentabilidade_valor',
                                     'coluna_proporcao', 'coluna_quantidade_documentos', 'coluna_ano_emissao',
                                     'coluna_mes_emissao', 'coluna_dia_emissao', 'coluna_media_dia',
                                     'coluna_documento',],

            'Filtros sobre Cliente': ['grupo_economico', 'carteira', 'carteira_parede_de_concreto',
                                      'carteira_premoldado_poste', 'tipo_cliente', 'cidade', 'estado',
                                      'informacao_estrategica',],
            'Filtros sobre Produto': ['familia_produto', 'produto',],
            'Filtros Gerais': ['job',],
        }

        return agrupamentos


class RelatoriosSupervisaoFaturamentosForm(RelatoriosSupervisaoBaseForm):
    nao_compraram_depois = forms.BooleanField(label="Não Compraram Depois do Periodo",
                                              help_text="e sem orçamentos em aberto", initial=False, required=False)

    def get_agrupamentos_campos(self):
        super_agrupamento = super().get_agrupamentos_campos()

        super_agrupamento['Filtros sobre Cliente'].append('nao_compraram_depois')

        return super_agrupamento


class RelatoriosSupervisaoOrcamentosForm(RelatoriosSupervisaoBaseForm):
    STATUS = STATUS_ORCAMENTOS_ITENS.objects

    status_orcamentos_itens = STATUS.all().order_by('DESCRICAO')
    status_orcamentos_itens_tipos = list(STATUS.values_list('TIPO', 'TIPO').distinct())
    status_orcamentos_itens_tipos.insert(0, ('', '---------'))
    status_orcamentos_itens_tipos.insert(1, ('PERDIDO_CANCELADO', 'PERDIDO OU CANCELADO'))

    coluna_status_produto_orcamento = forms.BooleanField(label="Coluna Status", initial=False, required=False)
    coluna_status_produto_orcamento_tipo = forms.BooleanField(label="Coluna Status Tipo", initial=False,
                                                              required=False)

    status_produto_orcamento = forms.ModelChoiceField(status_orcamentos_itens, label="Status", required=False)
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

        super_agrupamento['Visualizações sobre Produto'].append('coluna_status_produto_orcamento')
        super_agrupamento['Visualizações sobre Produto'].append('coluna_status_produto_orcamento_tipo')

        super_agrupamento['Filtros sobre Produto'].append('status_produto_orcamento')
        super_agrupamento['Filtros sobre Produto'].append('status_produto_orcamento_tipo')
        super_agrupamento['Filtros sobre Produto'].append('desconsiderar_justificativas')
        super_agrupamento['Filtros sobre Produto'].append('considerar_itens_excluidos')

        return super_agrupamento


class FormEventos(FormVendedoresMixIn, forms.Form):
    incluir_futuros = forms.BooleanField(label="Incluir Eventos Futuros", initial=False, required=False)


class FormEventosDesconsiderar(FormVendedoresMixIn, forms.Form):
    desconsiderar_futuros = forms.BooleanField(label="Desconsiderar grupos com eventos futuros", initial=False,
                                               required=False)
