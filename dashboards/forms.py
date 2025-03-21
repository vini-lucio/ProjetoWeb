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
    coluna_tipo_cliente = forms.BooleanField(label="Coluna Tipo de Cliente", initial=False, required=False)
    coluna_cidade = forms.BooleanField(label="Coluna Cidade Principal", initial=False, required=False)
    coluna_estado = forms.BooleanField(label="Coluna Estado Principal", initial=False, required=False)
    coluna_familia_produto = forms.BooleanField(label="Coluna Familia Produto", initial=False, required=False)
    coluna_produto = forms.BooleanField(label="Coluna Produto", initial=False, required=False)
    coluna_unidade = forms.BooleanField(label="Coluna Unidade Produto", initial=False, required=False)
    coluna_preco_tabela_inclusao = forms.BooleanField(label="Coluna Preço de Tabela do Produto (na inclusão)",
                                                      initial=False, required=False)
    coluna_preco_venda_medio = forms.BooleanField(label="Coluna Preço de Venda Medio", initial=False, required=False)
    coluna_quantidade = forms.BooleanField(label="Coluna Quantidade", initial=False, required=False)
    coluna_rentabilidade = forms.BooleanField(label="Coluna % Margem de Contribuição", initial=False, required=False)
    coluna_rentabilidade_valor = forms.BooleanField(label="Coluna Valor Margem de Contribuição", initial=False,
                                                    required=False)
    # TODO: coluna de porcentagem (proporção)

    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo de Cliente", required=False)
    cidade = forms.CharField(label="Cidade Principal", max_length=300, required=False)
    estado = forms.ModelChoiceField(estados, label="Estado Principal", required=False)
    familia_produto = forms.ModelChoiceField(familias_produtos, label="Familia Produto", required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)
    nao_compraram_depois = forms.BooleanField(label="Não Compraram Depois do Periodo", initial=False, required=False)
