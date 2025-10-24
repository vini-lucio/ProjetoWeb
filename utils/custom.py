class DefaultDict(dict):
    """Dict que retorna string em branco quando a chave não existe"""

    def __missing__(self, key):
        return ""
