from home.models import SiteSetup, AssistentesTecnicos, AssistentesTecnicosAgenda
from utils.data_hora_atual import hoje


def get_site_setup():
    return SiteSetup.objects.order_by('-id').first()


def get_assistentes_tecnicos():
    return AssistentesTecnicos.objects.filter(status='ativo').order_by('nome')


def get_assistentes_tecnicos_agenda():
    return AssistentesTecnicosAgenda.objects.filter(data__gte=hoje()).order_by('data')