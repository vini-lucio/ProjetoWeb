import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Ferias
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_funcionarios

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_funcionario = get_funcionarios()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_funcionario = estrangeiro_funcionario.filter(chave_migracao=item['funcionario']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_funcionario:
                # ########### alterar model do import #########################
                instancia = Ferias(
                    # ######## alterar campos json vs model e chave estrangeira
                    chave_migracao=item['chave_migracao'],
                    funcionario=fk_verdadeira_funcionario,
                    periodo_trabalhado_inicio=item['periodo_trabalhado_inicio'],
                    periodo_trabalhado_fim=item['periodo_trabalhado_fim'],
                    dias_ferias=item['dias_ferias'],
                    dias_desconsiderar=item['dias_desconsiderar'],
                    antecipar_abono=item['antecipar_abono'],
                    dias_abono=item['dias_abono'],
                    antecipar_13=item['antecipar_13'],
                    periodo_descanso_inicio=item['periodo_descanso_inicio'],
                    observacoes=item['observacoes'],
                    # ######## usar str() em float ############################
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
