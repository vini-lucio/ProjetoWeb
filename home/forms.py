from django import forms
from django.forms.widgets import CheckboxInput
from utils.base_forms import FormPesquisarMixIn


class ConfirmacaoMigrarCidades(forms.Form):
    confirma = forms.BooleanField(label="Confirmar?", widget=CheckboxInput(attrs={'id': 'confirma-migrar-cidades'}))


class PesquisarForm(FormPesquisarMixIn, forms.Form):
    ...
