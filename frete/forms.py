from django import forms
from utils.choices import sim_nao_branco
from utils.base_forms import FormPeriodoInicioFimMixIn
from utils.data_hora_atual import hoje_as_yyyymmdd
from home.models import Estados, Produtos
from frete.models import TransportadorasRegioesValores


class PesquisarOrcamentoFreteForm(forms.Form):
    rural = sim_nao_branco
    transportadoras_regioes_valores = TransportadorasRegioesValores.filter_ativos()

    orcamento = forms.IntegerField(label="nº Orçamento:")
    zona_rural = forms.ChoiceField(label="Destino Zona Rural?", choices=rural)  # type:ignore
    transportadora_valor_redespacho = forms.ModelChoiceField(transportadoras_regioes_valores,
                                                             label="Redespacho:", required=False)


class PesquisarCidadePrazosForm(forms.Form):
    uf = Estados.objects.all()

    uf_origem = forms.ModelChoiceField(uf, label="UF Origem", initial=uf.get(sigla="SP"))
    uf_destino = forms.ModelChoiceField(uf, label="UF Destino")
    cidade_destino = forms.CharField(label="Cidade Destino", max_length=70)


class PeriodoInicioFimForm(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()


class VolumesManualForm(forms.Form):
    produtos = Produtos.filter_ativos().filter(quantidade_volume__gt=0)

    produto = forms.ModelChoiceField(produtos, label="Produto")
    quantidade = forms.DecimalField(label="Quantidade")
