from django import forms
from rh.models import Setores
from utils.base_forms import BaseFormRelatoriosRh, FormPeriodoInicioFimMixIn, FormDataAssinaturaMixIn

# TODO: Documentar


class ReciboValeTransporteForm (FormDataAssinaturaMixIn, FormPeriodoInicioFimMixIn, BaseFormRelatoriosRh):
    ...


class FeriasEmAbertoForm (BaseFormRelatoriosRh):
    setores = Setores.objects.all()

    setor = forms.ModelChoiceField(setores, label="Setor")


class DependentesIrForm (FormDataAssinaturaMixIn, BaseFormRelatoriosRh):
    ...
