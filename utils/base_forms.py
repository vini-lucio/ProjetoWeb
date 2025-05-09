from django import forms
from django.forms.widgets import DateInput
from home.models import Jobs, Vendedores


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


class FormVendedoresMixIn(forms.Form):
    carteiras = Vendedores.objects.filter(canal_venda__descricao='CONSULTOR TECNICO')

    carteira = forms.ModelChoiceField(carteiras, label="Carteira")
