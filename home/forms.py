from django import forms
from django.forms.widgets import CheckboxInput
from utils.base_forms import FormPesquisarMixIn


class ConfirmacaoMigrar(forms.Form):
    confirma = forms.BooleanField(label="Confirmar?")
    # confirma = forms.BooleanField(label="Confirmar?", widget=CheckboxInput(attrs={'id': 'confirma-migrar-cidades'}))

    def __init__(self, *args, id_confirma: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['confirma'].widget = CheckboxInput(attrs={'id': id_confirma})


class PesquisarForm(FormPesquisarMixIn, forms.Form):
    ...
