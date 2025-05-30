from django import forms
from rh.models import Setores, Ferias
from utils.base_forms import BaseFormRelatoriosRh, FormPeriodoInicioFimMixIn, FormDataAssinaturaMixIn


class ReciboValeTransporteForm (FormDataAssinaturaMixIn, FormPeriodoInicioFimMixIn, BaseFormRelatoriosRh):
    ...


class FeriasEmAbertoForm (BaseFormRelatoriosRh):
    setores = Setores.objects.all()

    setor = forms.ModelChoiceField(setores, label="Setor")


class DependentesIrForm (FormDataAssinaturaMixIn, BaseFormRelatoriosRh):
    ...


class CamposFeriasMaiorForm(forms.ModelForm):
    class Meta:
        model = Ferias
        fields = '__all__'
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 4, 'cols': 80},)
        }
