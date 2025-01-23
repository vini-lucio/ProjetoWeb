from django import forms
from utils.choices import sim_nao_branco


class PesquisarOrcamentoFrete(forms.Form):
    rural = sim_nao_branco

    orcamento = forms.IntegerField(label="nº Orçamento:")
    zona_rural = forms.ChoiceField(label="Destino Zona Rural?", choices=rural)  # type:ignore
