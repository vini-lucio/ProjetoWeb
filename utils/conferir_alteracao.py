def campo_django_mudou(model, instancia, **kwargs) -> bool:
    """Retorna True ou False se algum campo passado em kwargs mudou.
    A chave do kwargs precisa ver o mesmo nome do campo"""
    anterior = model.objects.filter(pk=instancia.pk).first()
    for chave_novo, valor_novo in kwargs.items():
        if valor_novo != getattr(anterior, chave_novo):
            return True
    return False
