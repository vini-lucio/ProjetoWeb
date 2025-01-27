from django import forms
from utils.choices import sim_nao_branco
from home.models import Estados


class PesquisarOrcamentoFreteForm(forms.Form):
    rural = sim_nao_branco

    orcamento = forms.IntegerField(label="nº Orçamento:")
    zona_rural = forms.ChoiceField(label="Destino Zona Rural?", choices=rural)  # type:ignore


class PesquisarCidadePrazosForm(forms.Form):
    uf = Estados.objects.all()

    uf_origem = forms.ModelChoiceField(uf, label="UF Origem", initial=uf.get(sigla="SP"))
    uf_destino = forms.ModelChoiceField(uf, label="UF Destino")
    cidade_destino = forms.CharField(label="Cidade Destino", max_length=70)
