from django import forms
from utils.base_forms import FormPeriodoInicioFimMixIn
from analysis.models import VENDEDORES, CLIENTES_TIPOS
from utils.data_hora_atual import hoje_as_yyyymmdd


class RelatoriosSupervisaoForm(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()

    carteiras = VENDEDORES.objects.using('analysis').filter(CHAVE_CANAL=9).all().order_by('NOMERED')
    clientes_tipos = CLIENTES_TIPOS.objects.using('analysis').all().order_by('DESCRICAO')

    coluna_grupo_economico = forms.BooleanField(label="Coluna Grupo Economico", initial=True, required=False)
    grupo_economico = forms.CharField(label="Grupo Economico", max_length=300, required=False)

    coluna_carteira = forms.BooleanField(label="Coluna Carteira", initial=True, required=False)
    carteira = forms.ModelChoiceField(carteiras, label="Carteira", required=False)

    coluna_tipo_cliente = forms.BooleanField(label="Coluna Tipo de Cliente", initial=False, required=False)
    tipo_cliente = forms.ModelChoiceField(clientes_tipos, label="Tipo de Cliente", required=False)

    coluna_produto = forms.BooleanField(label="Coluna Produto", initial=False, required=False)
    produto = forms.CharField(label="Produto", max_length=300, required=False)

    nao_compraram_depois = forms.BooleanField(label="Não Compraram Depois do Periodo", initial=False, required=False)

    coluna_rentabilidade = forms.BooleanField(label="Coluna Margem de Contribuição", initial=False, required=False)
