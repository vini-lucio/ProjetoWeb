from django.db.models import Max

# TODO: Documentar


def get_funcionarios_ativos(funcionarios):
    return funcionarios.filter(data_saida__isnull=True).all()


def get_funcionarios_salarios_atuais(funcionarios, somente_ativos=True):
    # ################ essa função funciona, mas usar model de FuncionariosSalarioFuncaoAtual
    if somente_ativos:
        funcionarios = get_funcionarios_ativos(funcionarios)
    funcionarios_com_maior_data = funcionarios.annotate(maior_data=Max("salarios__data"))
    salarios_atuais = []
    for funcionario in funcionarios_com_maior_data:
        salarios_funcionario = funcionario.salarios.all()
        if salarios_funcionario:
            salarios_atuais.append(salarios_funcionario.get(data=funcionario.maior_data))
    return salarios_atuais
