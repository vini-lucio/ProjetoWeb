from django import forms


class Confirmacao(forms.Form):
    confirma = forms.BooleanField(label="Confirmar?")
