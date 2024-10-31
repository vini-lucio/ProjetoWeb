import json
from home.models import Jobs
from pathlib import Path
from django.core.management.base import BaseCommand

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'JOBS.json'


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            instancia = Jobs(
                descricao=item['descricao'],
                chave_migracao=item['chave_migracao'],
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
