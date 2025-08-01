from background_task import background
from background_task.models import Task, CompletedTask
from analysis.models import ORCAMENTOS
from dashboards.models import MetasCarteiras
from home.models import ControleInscricoesEstaduais, InscricoesEstaduais, Estados
from django.conf import settings
from django.utils import timezone
from django.db.models import Max
from utils.converter import somente_digitos
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import datetime
import time


hoje = timezone.localtime().date()
agora = timezone.now()


@background(remove_existing_tasks=True)
def atualiza_metas_carteiras_valores():
    MetasCarteiras.atualizar_metas_carteiras_valores()


atualiza_metas_carteiras_valores_hora = datetime.time(hour=20, minute=00)
atualiza_metas_carteiras_valores_agenda = timezone.make_aware(
    datetime.datetime.combine(hoje, atualiza_metas_carteiras_valores_hora)
)
atualiza_metas_carteiras_valores(schedule=atualiza_metas_carteiras_valores_agenda, repeat=Task.DAILY)  # type:ignore


@background(remove_existing_tasks=True)
def confere_inscricoes_api():
    somente_digitos_ = somente_digitos
    conferencia = timezone.now()

    controle_inscricao_estadual = ControleInscricoesEstaduais.objects.first()

    if not controle_inscricao_estadual:
        return

    if conferencia < controle_inscricao_estadual.ultima_conferencia + datetime.timedelta(minutes=7):
        return

    documentos_conferir = ORCAMENTOS.objects.filter(CHAVE__gt=controle_inscricao_estadual.ultimo_documento)
    ultimo_documento_conferido = documentos_conferir.aggregate(Max('CHAVE'))['CHAVE__max']

    if ultimo_documento_conferido:
        controle_inscricao_estadual.ultimo_documento = ultimo_documento_conferido
    controle_inscricao_estadual.ultima_conferencia = conferencia
    controle_inscricao_estadual.full_clean()
    controle_inscricao_estadual.save()

    documentos_conferir_pessoas_jurudicas = documentos_conferir.filter(CHAVE_CLIENTE__TIPO='PESSOA JURIDICA')
    if not documentos_conferir_pessoas_jurudicas.exists():
        return

    cnpjs = documentos_conferir_pessoas_jurudicas.values_list('CHAVE_CLIENTE__CGC', flat=True)
    # TODO: fazer um append com cnpjs dos canteiros (pedidos?)

    for cnpj in cnpjs:
        cnpj_numeros = somente_digitos_(cnpj)

        inscricoes = InscricoesEstaduais.objects.filter(cnpj=cnpj)
        inscricoes_existe = inscricoes.first()

        if inscricoes_existe:
            if conferencia < inscricoes_existe.ultima_conferencia + datetime.timedelta(days=30):
                continue

        url_api = f'https://open.cnpja.com/office/{cnpj_numeros}'
        time.sleep(15)
        try:
            with urlopen(url_api) as response_api:
                api_data = json.load(response_api)
        except HTTPError:
            continue
        inscricoes_api = api_data.get('registrations', 'erro')

        if inscricoes_api == 'erro':
            continue

        if not inscricoes_api:
            inscricoes_nao_nulas = inscricoes.filter(inscricao_estadual__isnull=False, estado__isnull=False)
            if inscricoes_nao_nulas.exists():
                inscricoes_nao_nulas.delete()
            instancia, criado = InscricoesEstaduais.objects.update_or_create(
                cnpj=cnpj,
                inscricao_estadual__isnull=True,
                estado__isnull=True,
                defaults={
                    'cnpj': cnpj,
                    'inscricao_estadual': None,
                    'estado': None,
                    'habilitado': True,
                    'ultima_conferencia': conferencia,
                },
            )
            instancia.full_clean()
            instancia.save()
            continue

        for inscricao_api in inscricoes_api:
            estado_inscricao_api = Estados.objects.filter(sigla=inscricao_api.get('state')).first()
            instancia, criado = InscricoesEstaduais.objects.update_or_create(
                cnpj=cnpj,
                inscricao_estadual=inscricao_api.get('number'),
                estado=estado_inscricao_api,
                defaults={
                    'cnpj': cnpj,
                    'inscricao_estadual': inscricao_api.get('number'),
                    'estado': estado_inscricao_api,
                    'habilitado': inscricao_api.get('enabled'),
                    'ultima_conferencia': conferencia,
                },
            )
            instancia.full_clean()
            instancia.save()

        inscricoes_inexistentes = InscricoesEstaduais.objects.filter(
            cnpj=cnpj).exclude(ultima_conferencia=conferencia)
        if inscricoes_inexistentes.exists():
            inscricoes_inexistentes.delete()


if not settings.DEBUG:
    confere_inscricoes_api_agenda = agora + datetime.timedelta(minutes=10)
    confere_inscricoes_api(schedule=confere_inscricoes_api_agenda, repeat=600)  # type:ignore


@background(remove_existing_tasks=True)
def limpar_completed_tasks():
    dia_anterior = timezone.now() - datetime.timedelta(days=1)
    completed_tasks = CompletedTask.objects.filter(run_at__lt=dia_anterior)
    completed_tasks.delete()


limpar_completed_tasks_hora = datetime.time(hour=23, minute=50)
limpar_completed_tasks_agenda = timezone.make_aware(
    datetime.datetime.combine(hoje, limpar_completed_tasks_hora)
)
limpar_completed_tasks(schedule=limpar_completed_tasks_agenda, repeat=Task.DAILY)  # type:ignore
