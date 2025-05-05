from django import forms
from django.forms.widgets import DateInput
from home.models import Jobs
from analysis.models import VENDEDORES


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
    carteiras = VENDEDORES.objects.using('analysis').filter(CHAVE_CANAL=9).all().order_by('NOMERED')

    carteira = forms.ModelChoiceField(carteiras, label="Carteira")
