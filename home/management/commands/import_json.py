import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from home.models import Cidades
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_estados

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get e for ######################################
estrangeiro = get_estados()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira = estrangeiro.filter(chave_migracao=item['estado']).first()
            # ########### alterar model do import #############################
            instancia = Cidades(
                # ########### alterar campos json vs model e chave estrangeira
                chave_migracao=item['chave_migracao'],
                chave_analysis=item['chave_analysis'],
                estado=fk_verdadeira,
                nome=item['nome'],
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
