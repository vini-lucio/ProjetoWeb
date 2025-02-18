from django import forms
from utils.choices import sim_nao_branco
from utils.base_forms import FormPeriodoInicioFimMixIn
from utils.data_hora_atual import hoje_as_yyyymmdd
from home.models import Estados, Produtos
from frete.models import TransportadorasRegioesValores, Transportadoras


class TransportadoraValorFormMixIn(forms.Form):
    transportadoras_regioes_valores = TransportadorasRegioesValores.filter_ativos()

    transportadora_valor = forms.ModelChoiceField(transportadoras_regioes_valores, required=False)


class ReajustesForm(forms.Form):
    transportadoras = Transportadoras.filter_ativos()
    campos = [(field.name, field.verbose_name) for field in TransportadorasRegioesValores._meta.get_fields()  # type:ignore
              if field.get_internal_type() == 'DecimalField']
    campos.append(('', '---------'))
    campos.append(('margem_kg_valor', 'Margem (kg) R$'))
    campos.sort()

    transportadora = forms.ModelChoiceField(transportadoras, label="Transportadora")
    campo = forms.ChoiceField(label="Campo", choices=campos, initial='')  # type:ignore
    reajuste = forms.DecimalField(label="Reajuste %", required=False)


class PesquisarOrcamentoFreteForm(TransportadoraValorFormMixIn, forms.Form):
    rural = sim_nao_branco
    transportadoras_regioes_valores = TransportadorasRegioesValores.filter_ativos()

    orcamento = forms.IntegerField(label="nº Orçamento:")
    zona_rural = forms.ChoiceField(label="Destino Zona Rural?", choices=rural)  # type:ignore

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo_no_final = self.fields.pop('transportadora_valor')
        self.fields.update({'transportadora_valor': campo_no_final})
        self.fields['transportadora_valor'].label = 'Redespacho:'


class PesquisarCidadePrazosForm(forms.Form):
    uf = Estados.objects.all()

    # TODO: voltar linha comentada apos migração e importação em produção
    # uf_origem = forms.ModelChoiceField(uf, label="UF Origem", initial=uf.get(sigla="SP"))
    uf_origem = forms.ModelChoiceField(uf, label="UF Origem")
    uf_destino = forms.ModelChoiceField(uf, label="UF Destino")
    cidade_destino = forms.CharField(label="Cidade Destino", max_length=70)


class PeriodoInicioFimForm(FormPeriodoInicioFimMixIn, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inicio'].initial = hoje_as_yyyymmdd()
        self.fields['fim'].initial = hoje_as_yyyymmdd()


class VolumesManualForm(TransportadoraValorFormMixIn, forms.Form):
    produtos = Produtos.filter_ativos().filter(quantidade_volume__gt=0)

    valor_total = forms.DecimalField(label="(Opcional) Valor Total", required=False)
    produto = forms.ModelChoiceField(produtos, label="Produto")
    quantidade = forms.DecimalField(label="Quantidade")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transportadora_valor'].label = '(Opcional) Tabela Transportadora:'
