from django import forms
from django.forms.widgets import DateInput
from home.models import Jobs
from rh.models import Setores


class ReciboValeTransporteForm (forms.Form):
    jobs = Jobs.objects.all()

    inicio = forms.DateField(label="Periodo Inicio", widget=DateInput(attrs={'type': 'date'}))
    fim = forms.DateField(label="Periodo Fim", widget=DateInput(attrs={'type': 'date'}))
    assinatura = forms.DateField(label="Data Assinatura", widget=DateInput(attrs={'type': 'date'}))
    job = forms.ModelChoiceField(jobs, label="Job")


class FeriasEmAbertoForm (forms.Form):
    jobs = Jobs.objects.all()
    setores = Setores.objects.all()

    job = forms.ModelChoiceField(jobs, label="Job")
    setor = forms.ModelChoiceField(setores, label="Setor")
