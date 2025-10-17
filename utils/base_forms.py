from django import forms
from django.db.models import Q
from django.forms.widgets import DateInput
from home.models import Jobs, Vendedores

# TODO: Documentar


class BaseFormRelatoriosRh(forms.Form):
    jobs = Jobs.objects.all()

    job = forms.ModelChoiceField(jobs, label="Job")


class FormPeriodoInicioFimMixIn(forms.Form):
    inicio = forms.DateField(label="Periodo Inicio", widget=DateInput(attrs={'type': 'date'}))
    fim = forms.DateField(label="Periodo Fim", widget=DateInput(attrs={'type': 'date'}))


class FormDataAssinaturaMixIn(forms.Form):
    assinatura = forms.DateField(label="Data Assinatura", widget=DateInput(attrs={'type': 'date'}))


class FormPesquisarMixIn(forms.Form):
    pesquisar = forms.CharField(label="Pesquisar", max_length=300)


class FormPesquisarIntegerMixIn(forms.Form):
    pesquisar = forms.IntegerField(label="Pesquisar")


class FormVendedoresMixIn(forms.Form):
    carteiras = Vendedores.objects.filter(Q(canal_venda__descricao='CONSULTOR TECNICO') | Q(nome='ZZENCERRADO'))

    carteira = forms.ModelChoiceField(carteiras, label="Carteira")


class FormCampoGrandeMixIn(forms.ModelForm):
    campos_redimensionar = []

    class Meta:
        model = None
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.campos_redimensionar:
            if campo in self.fields:
                self.fields[campo].widget = forms.Textarea(attrs={'rows': 4, 'cols': 80})


def criar_form_campo_grande(model_, campos_redimensionar_: list):
    class FormCampoGrandeDinamico(FormCampoGrandeMixIn):
        class Meta:
            model = model_
            fields = '__all__'
        campos_redimensionar = campos_redimensionar_

    return FormCampoGrandeDinamico
