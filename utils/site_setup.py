from home.models import (SiteSetup, AssistentesTecnicos, AssistentesTecnicosAgenda, Estados, Cidades, Jobs, Paises,
                         Bancos, Unidades)
from rh.models import (Cbo, Escolaridades, Funcionarios, DependentesTipos, Horarios, TransporteLinhas, TransporteTipos,
                       ValeTransportes, Setores, Funcoes)
from utils.data_hora_atual import hoje


def get_site_setup():
    return SiteSetup.objects.order_by('-id').first()


def get_cores_rentabilidade():
    SITE_SETUP = get_site_setup()

    if not SITE_SETUP:
        return {}

    verde = SITE_SETUP.rentabilidade_verde_as_float
    amarelo = SITE_SETUP.rentabilidade_amarela_as_float
    vermelho = SITE_SETUP.rentabilidade_vermelha_as_float
    despesa_adm = SITE_SETUP.despesa_administrativa_fixa_as_float

    return {'verde': verde, 'amarelo': amarelo, 'vermelho': vermelho, 'despesa_adm': despesa_adm}


def get_assistentes_tecnicos():
    return AssistentesTecnicos.objects.filter(status='ativo').order_by('nome')


def get_assistentes_tecnicos_agenda():
    return AssistentesTecnicosAgenda.objects.filter(data__gte=hoje()).order_by('data')


def get_estados():
    return Estados.objects


def get_cidades():
    return Cidades.objects


def get_jobs():
    return Jobs.objects


def get_cbo():
    return Cbo.objects


def get_escolaridades():
    return Escolaridades.objects


def get_paises():
    return Paises.objects


def get_bancos():
    return Bancos.objects


def get_funcionarios():
    return Funcionarios.objects


def get_dependentes_tipos():
    return DependentesTipos.objects


def get_horarios():
    return Horarios.objects


def get_transporte_linhas():
    return TransporteLinhas.objects


def get_transporte_tipos():
    return TransporteTipos.objects


def get_vale_transportes():
    return ValeTransportes.objects


def get_setores():
    return Setores.objects


def get_funcoes():
    return Funcoes.objects


def get_unidades():
    return Unidades.objects
