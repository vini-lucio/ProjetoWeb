from django import forms
from django.forms.widgets import CheckboxInput
from utils.base_forms import FormPesquisarMixIn, FormPeriodoInicioFimMixIn


class ConfirmacaoMigrar(forms.Form):
    confirma = forms.BooleanField(label="Confirmar?")
    # confirma = forms.BooleanField(label="Confirmar?", widget=CheckboxInput(attrs={'id': 'confirma-migrar-cidades'}))

    def __init__(self, *args, id_confirma: str, **kwargs):
        """
        Parametros:
        -----------
        :id_confirma (str): id para o elemento html do campo confirma do formulario
        """
        super().__init__(*args, **kwargs)
        self.fields['confirma'].widget = CheckboxInput(attrs={'id': id_confirma})


class PesquisarForm(FormPesquisarMixIn, forms.Form):
    ...


class ConfirmacaoMigrarDataFimNonRequired(FormPeriodoInicioFimMixIn, ConfirmacaoMigrar):
    def __init__(self, *args, id_confirma: str, **kwargs):
        super().__init__(*args, id_confirma=id_confirma, **kwargs)
        self.fields['fim'].required = False


class ConfirmacaoMigrarData(FormPeriodoInicioFimMixIn, ConfirmacaoMigrar):
    ...
