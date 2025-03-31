from django import forms
from utils.base_forms import FormPeriodoInicioFimMixIn
from analysis.models import VENDEDORES, CLIENTES_TIPOS, FAIXAS_CEP, ESTADOS, FAMILIA_PRODUTOS, STATUS_ORCAMENTOS_ITENS
from utils.data_hora_atual import hoje_as_yyyymmdd


class RelatoriosSupervisaoBaseForm(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()

    carteiras = VENDEDORES.objects.using('analysis').filter(CHAVE_CANAL=9).all().order_by('NOMERED')
    clientes_tipos = CLIENTES_TIPOS.objects.using('analysis').all().order_by('DESCRICAO')
    cidades = FAIXAS_CEP.objects.using('analysis').all().order_by('CIDADE')
    estados = ESTADOS.objects.using('analysis').all().order_by('ESTADO')
    familias_produtos = FAMILIA_PRODUTOS.objects.using('analysis').all().order_by('FAMILIA')

    coluna_grupo_economico = forms.BooleanField(label="Coluna Grupo Economico", initial=True, required=False)
    coluna_carteira = forms.BooleanField(label="Coluna Carteira", initial=True, required=False)
    coluna_tipo_cliente = forms.BooleanField(label="Coluna Tipo", initial=False, required=False)
    coluna_cidade = forms.BooleanField(label="Coluna Cidade Principal", initial=False, required=False)
    coluna_estado = forms.BooleanField(label="Coluna Estado Principal", initial=False, required=False)
    coluna_familia_produto = forms.BooleanField(label="Coluna Familia", initial=False, required=False)
    coluna_produto = forms.BooleanField(label="Coluna Produto", initial=False, required=False)
    coluna_unidade = forms.BooleanField(label="Coluna Unidade", initial=False, required=False)
    coluna_preco_tabela_inclusao = forms.BooleanField(label="Coluna Preço de Tabela R$", help_text="na inclusão, maior",
                                                      initial=False, required=False)
    coluna_preco_venda_medio = forms.BooleanField(label="Coluna Preço Medio R$", initial=False, required=False)
    coluna_quantidade = forms.BooleanField(label="Coluna Quantidade", initial=False, required=False)
    coluna_rentabilidade = forms.BooleanField(label="Coluna % MC", initial=False, required=False)
    coluna_rentabilidade_valor = forms.BooleanField(label="Coluna R$ MC", initial=False,
                                                    required=False)
    coluna_proporcao = forms.BooleanField(label="Coluna % Proporção", initial=True, required=False)
    coluna_quantidade_documentos = forms.BooleanField(label="Coluna Quantidade de Documentos", initial=False,
                                                      required=False)
    coluna_ano_emissao = forms.BooleanField(label="Coluna Ano Emissão", initial=False, required=False)
    coluna_mes_emissao = forms.BooleanField(label="Coluna Mês Emissão", initial=False, required=False)
    coluna_media_dia = forms.BooleanField(label="Coluna R$ Médio por Dia", help_text="de venda", initial=False,
                                          required=False)

    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo", required=False)
    cidade = forms.CharField(label="Cidade Principal", max_length=300, required=False)
    estado = forms.ModelChoiceField(estados, label="Estado Principal", required=False)
    familia_produto = forms.ModelChoiceField(familias_produtos, label="Familia", required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)

    def get_agrupamentos_campos(self):
        agrupamentos = {
            'Data de Emissao': ['inicio', 'fim',],

            'Visualizações sobre Cliente': ['coluna_grupo_economico', 'coluna_carteira', 'coluna_tipo_cliente',
                                            'coluna_cidade', 'coluna_estado',],
            'Visualizações sobre Produto': ['coluna_familia_produto', 'coluna_produto', 'coluna_unidade',
                                            'coluna_preco_tabela_inclusao', 'coluna_preco_venda_medio',
                                            'coluna_quantidade',],
            'Visualizações Gerais': ['coluna_rentabilidade', 'coluna_rentabilidade_valor', 'coluna_proporcao',
                                     'coluna_quantidade_documentos', 'coluna_ano_emissao', 'coluna_mes_emissao',
                                     'coluna_media_dia',],

            'Filtros sobre Cliente': ['grupo_economico', 'carteira', 'tipo_cliente',
                                      'cidade', 'estado',],
            'Filtros sobre Produto': ['familia_produto', 'produto',],
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
    STATUS = STATUS_ORCAMENTOS_ITENS.objects.using('analysis')

    status_orcamentos_itens = STATUS.all().order_by('DESCRICAO')
    status_orcamentos_itens_tipos = list(STATUS.values_list('TIPO', 'TIPO').distinct())
    status_orcamentos_itens_tipos.insert(0, ('', '---------'))
    status_orcamentos_itens_tipos.insert(1, ('PERDIDO_CANCELADO', 'PERDIDO OU CANCELADO'))

    coluna_status_produto_orcamento = forms.BooleanField(label="Coluna Status", help_text="exceto excluidos",
                                                         initial=False, required=False)
    coluna_status_produto_orcamento_tipo = forms.BooleanField(label="Coluna Status Tipo", help_text="exceto excluidos",
                                                              initial=False, required=False)

    status_produto_orcamento = forms.ModelChoiceField(status_orcamentos_itens, label="Status",
                                                      help_text="exceto excluidos", required=False)
    status_produto_orcamento_tipo = forms.ChoiceField(label="Status Tipo", help_text="exceto excluidos",
                                                      choices=status_orcamentos_itens_tipos, initial=False,
                                                      required=False)
    desconsiderar_justificativas = forms.BooleanField(label="Desconsiderar Justificativas Invalidas",
                                                      help_text="de orçamentos não fechados (exceto excluidos)",
                                                      initial=True, required=False)

    def get_agrupamentos_campos(self):
        super_agrupamento = super().get_agrupamentos_campos()

        super_agrupamento['Visualizações sobre Produto'].append('coluna_status_produto_orcamento')
        super_agrupamento['Visualizações sobre Produto'].append('coluna_status_produto_orcamento_tipo')

        super_agrupamento['Filtros sobre Produto'].append('status_produto_orcamento')
        super_agrupamento['Filtros sobre Produto'].append('status_produto_orcamento_tipo')
        super_agrupamento['Filtros sobre Produto'].append('desconsiderar_justificativas')

        return super_agrupamento
