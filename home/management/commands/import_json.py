import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Horarios
# ########### alterar/comentar get do import ##################################
# from utils.site_setup import get_cbo

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
# estrangeiro = get_cbo()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            # fk_verdadeira = estrangeiro.filter(chave_migracao=item['cbo']).first()
            # ########### alterar model do import #############################
            instancia = Horarios(
                # ########### alterar campos json vs model e chave estrangeira
                # ########### usar str() em float #############################
                chave_migracao=item['chave_migracao'],
                inicio=item['inicio'],
                fim=item['fim'],
                intervalo_inicio=item['intervalo_inicio'],
                intervalo_fim=item['intervalo_fim'],
                sexta_fim=item['sexta_fim'],
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
