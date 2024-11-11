from home.models import SiteSetup, AssistentesTecnicos, AssistentesTecnicosAgenda, Estados, Cidades, Jobs, Paises, Bancos
from rh.models import Cbo, Escolaridades, Funcionarios
from utils.data_hora_atual import hoje


def get_site_setup():
    return SiteSetup.objects.order_by('-id').first()


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
