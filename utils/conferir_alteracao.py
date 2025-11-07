def campo_django_mudou(model, instancia, **kwargs) -> bool:
    """Verifica se uma instancia de um model sofreu alterações. Usar quando sobreescrever save ou clean de um model.

    Parametros:
    -----------
    :model [Model]: com o model a ser verificado.
    :instancia [model]: com a instancia do model a ser verificada.
    :kwargs [dict]: com os campos a serem verificados, onde a chave é o nome do campo e o valor é o seu conteudo.

    Retorno:
    --------
    :bool: booleado se houve alteração."""
    anterior = model.objects.filter(pk=instancia.pk).first()
    if anterior:
        for chave_novo, valor_novo in kwargs.items():
            if valor_novo != getattr(anterior, chave_novo):
                return True
    return False


def campo_migrar_mudou(objeto_destino, objeto_origem, mapeamento_destino_origem) -> bool:
    """Verifica se objetos de origem e destino possuem os campos informados diferentes.

    Parametros:
    -----------
    :objeto_destino [model]: com o objeto de destino da comparação.
    :objeto_origem [model]: com o objeto de origem da comparação.
    :mapeamento_destino_origem [dict[str, str | tuple[str, tuple[str, str]]]]: com a relação de campos. Quando campo
    não for chave estrangeira a chave é o campo_destino e valor é o campo_origem, ex: 'nome': 'CIDADE'. Se o campo for
    chave estrangeira a chave é o campo_destino e o valor é uma tupla com o campo_destino e outra tupla com o campo da chave estrangeira do destino e campo da chave estrangeira da origem, ex: 'estado': ('UF', ('sigla', 'SIGLA')).

    >>> mapeamento_destino_origem = {
        'estado': ('UF', ('sigla', 'SIGLA')),
        'nome': 'CIDADE',
    }

    Retorno:
    --------
    :bool: boolano se algum dos campos informados são diferentes entre os objetos."""
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
            destino = get_attr(destino, fk_key_destino) if destino else None
            origem = get_attr(origem, fk_value_origem) if origem else None

        if (destino != origem) or (origem and not destino) or (not origem and destino):
            return True

    return False
