from background_task import background
from background_task.models import Task
from dashboards.models import MetasCarteiras
from django.utils import timezone
import datetime


@background(remove_existing_tasks=True)
def atualiza_metas_carteiras_valores():
    MetasCarteiras.atualizar_metas_carteiras_valores()


hoje = timezone.localtime().date()

atualiza_metas_carteiras_valores_hora = datetime.time(hour=20, minute=00)
atualiza_metas_carteiras_valores_agenda = timezone.make_aware(
    datetime.datetime.combine(hoje, atualiza_metas_carteiras_valores_hora)
)
atualiza_metas_carteiras_valores(schedule=atualiza_metas_carteiras_valores_agenda, repeat=Task.DAILY)  # type:ignore
