import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Afastamentos
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_funcionarios

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro = get_funcionarios()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira = estrangeiro.filter(chave_migracao=item['funcionario']).first()
            # ########### alterar model do import #############################
            instancia = Afastamentos(
                # ########### alterar campos json vs model e chave estrangeira
                # ########### usar str() em float #############################
                chave_migracao=item['chave_migracao'],
                funcionario=fk_verdadeira,
                data_afastamento=item['data_afastamento'],
                data_previsao_retorno=item['data_previsao_retorno'],
                data_retorno=item['data_retorno'],
                motivo=item['motivo'],
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
