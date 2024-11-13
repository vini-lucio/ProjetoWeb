import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import ValeTransportesFuncionarios
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_vale_transportes, get_funcionarios

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_vale_transporte = get_vale_transportes()
estrangeiro_funcionario = get_funcionarios()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_vale_transporte = estrangeiro_vale_transporte.filter(
                linha__chave_migracao=item['vale_transporte_linha'],
                tipo__chave_migracao=item['vale_transporte_tipo']).first()
            fk_verdadeira_funcionario = estrangeiro_funcionario.filter(chave_migracao=item['funcionario']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_funcionario:
                # ########### alterar model do import #########################
                instancia = ValeTransportesFuncionarios(
                    # ######## alterar campos json vs model e chave estrangeira
                    chave_migracao=item['chave_migracao'],
                    funcionario=fk_verdadeira_funcionario,
                    vale_transporte=fk_verdadeira_vale_transporte,
                    quantidade_por_dia=item['quantidade_por_dia'],
                    dias=item['dias'],
                    # ######## usar str() em float ############################
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
