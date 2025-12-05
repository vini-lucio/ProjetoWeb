from django.db.models import Max


def get_funcionarios_ativos(funcionarios):
    return funcionarios.filter(data_saida__isnull=True).all()


def get_funcionarios_salarios_atuais(funcionarios, somente_ativos=True):
    """Função similar ao model de FuncionariosSalarioFuncaoAtual.

    Retorna lista com salarios atuais de funcionarios.

    Parametros:
    -----------
    :funcionarios (Funcionarios): com filtro de funcionarios
    :somente_ativos (bool, Default True): booleano se somente funcionarios ativos

    Retorno:
    --------
    :lista[Salarios]: com o salario atual dos funcionarios"""
    if somente_ativos:
        funcionarios = get_funcionarios_ativos(funcionarios)
    funcionarios_com_maior_data = funcionarios.annotate(maior_data=Max("salarios__data"))
    salarios_atuais = []
    for funcionario in funcionarios_com_maior_data:
        salarios_funcionario = funcionario.salarios.all()
        if salarios_funcionario:
            salarios_atuais.append(salarios_funcionario.get(data=funcionario.maior_data))
    return salarios_atuais
