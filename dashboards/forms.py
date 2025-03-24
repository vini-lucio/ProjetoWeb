from django import forms
from utils.base_forms import FormPeriodoInicioFimMixIn
from analysis.models import VENDEDORES, CLIENTES_TIPOS, FAIXAS_CEP, ESTADOS, FAMILIA_PRODUTOS
from utils.data_hora_atual import hoje_as_yyyymmdd


class RelatoriosSupervisaoForm(FormPeriodoInicioFimMixIn, forms.Form):
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
    coluna_preco_tabela_inclusao = forms.BooleanField(label="Coluna Preço de Tabela", help_text="na inclusão",
                                                      initial=False, required=False)
    coluna_preco_venda_medio = forms.BooleanField(label="Coluna Preço Medio", initial=False, required=False)
    coluna_quantidade = forms.BooleanField(label="Coluna Quantidade", initial=False, required=False)
    coluna_rentabilidade = forms.BooleanField(label="Coluna % MC", initial=False, required=False)
    coluna_rentabilidade_valor = forms.BooleanField(label="Coluna Valor MC", initial=False,
                                                    required=False)
    coluna_proporcao = forms.BooleanField(label="Coluna % Proporção", initial=True, required=False)
    coluna_quantidade_notas = forms.BooleanField(label="Coluna Quantidade de Notas", initial=False, required=False)

    # TODO: resto das colunas relatorios Salomão

    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo", required=False)
    cidade = forms.CharField(label="Cidade Principal", max_length=300, required=False)
    estado = forms.ModelChoiceField(estados, label="Estado Principal", required=False)
    familia_produto = forms.ModelChoiceField(familias_produtos, label="Familia Produto", required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)
    nao_compraram_depois = forms.BooleanField(label="Não Compraram Depois do Periodo",
                                              help_text="e sem orçamentos em aberto", initial=False, required=False)

    def get_agrupamentos_campos(self):
        agrupamentos = {
            'Data de Emissao': ['inicio', 'fim',],

            'Visualizações sobre Cliente': ['coluna_grupo_economico', 'coluna_carteira', 'coluna_tipo_cliente',
                                            'coluna_cidade', 'coluna_estado',],
            'Visualizações sobre Produto': ['coluna_familia_produto', 'coluna_produto', 'coluna_unidade',
                                            'coluna_preco_tabela_inclusao', 'coluna_preco_venda_medio',
                                            'coluna_quantidade',],
            'Visualizações Gerais': ['coluna_rentabilidade', 'coluna_rentabilidade_valor', 'coluna_proporcao',
                                     'coluna_quantidade_notas',],

            'Filtros sobre Cliente': ['grupo_economico', 'carteira', 'tipo_cliente',
                                      'cidade', 'estado',],
            'Filtros sobre Produto': ['familia_produto', 'produto',],
            'Filtros Gerais': ['nao_compraram_depois',],
        }

        return agrupamentos
