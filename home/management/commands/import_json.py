import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import HorariosFuncionarios
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_funcionarios, get_horarios

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_funcionario = get_funcionarios()
estrangeiro_horario = get_horarios()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_funcionario = estrangeiro_funcionario.filter(chave_migracao=item['funcionario']).first()
            fk_verdadeira_horario = estrangeiro_horario.filter(chave_migracao=item['horario']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_funcionario:
                # ########### alterar model do import #########################
                instancia = HorariosFuncionarios(
                    # ######## alterar campos json vs model e chave estrangeira
                    # ######## usar str() em float ############################
                    # chave_migracao=item['chave_migracao'],
                    funcionario=fk_verdadeira_funcionario,
                    horario=fk_verdadeira_horario,
                    dias=item['dias'],
                    data_inicio=item['data_inicio'],
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
