import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import ValeTransportes
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_transporte_linhas, get_transporte_tipos

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_linhas = get_transporte_linhas()
estrangeiro_tipos = get_transporte_tipos()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_linha = estrangeiro_linhas.filter(chave_migracao=item['linha']).first()
            fk_verdadeira_tipo = estrangeiro_tipos.filter(chave_migracao=item['tipo']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            # if fk_verdadeira_funcionario:
            # ########### alterar model do import #########################
            instancia = ValeTransportes(
                # ######## alterar campos json vs model e chave estrangeira
                chave_migracao=item['chave_migracao'],
                linha=fk_verdadeira_linha,
                tipo=fk_verdadeira_tipo,
                valor_unitario=str(item['valor_unitario']),
                quantidade_por_dia=item['quantidade_por_dia'],
                dias=item['dias'],
                # ######## usar str() em float ############################
            )
            instancia.full_clean()
            instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
