from django import forms
from django.forms.widgets import CheckboxInput


class ConfirmacaoMigrarCidades(forms.Form):
    confirma = forms.BooleanField(label="Confirmar?", widget=CheckboxInput(attrs={'id': 'confirma-migrar-cidades'}))
