def campo_django_mudou(model, instancia, **kwargs) -> bool:
    """Retorna True ou False se algum campo passado em kwargs mudou.
    A chave do kwargs precisa ser o mesmo nome do campo"""
    anterior = model.objects.filter(pk=instancia.pk).first()
    if anterior:
        for chave_novo, valor_novo in kwargs.items():
            if valor_novo != getattr(anterior, chave_novo):
                return True
    return False


def campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem) -> bool:
    if not objeto_destino:
        return True

    # armazenar em variaveis locais é mais rapido
    get_attr = getattr
    for key_destino, value_origem in mapeamento_destino_origem.items():
        destino = get_attr(objeto_destino, key_destino)

        if not isinstance(value_origem, tuple):
            origem = get_attr(objeto_origem, value_origem)

        else:
            value_origem, mapeamento_fk_destino_origem = value_origem
            origem = get_attr(objeto_origem, value_origem)

            fk_key_destino, fk_value_origem = mapeamento_fk_destino_origem
            destino = get_attr(destino, fk_key_destino)
            origem = get_attr(origem, fk_value_origem)

        if destino != origem:
            return True

    return False
