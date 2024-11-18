import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Salarios
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_funcionarios, get_setores, get_funcoes

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_funcionario = get_funcionarios()
estrangeiro_setor = get_setores()
estrangeiro_funcao = get_funcoes()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_funcionario = estrangeiro_funcionario.filter(chave_migracao=item['funcionario']).first()
            fk_verdadeira_setor = estrangeiro_setor.filter(chave_migracao=item['setor']).first()
            fk_verdadeira_funcao = estrangeiro_funcao.filter(chave_migracao=item['funcao']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_funcionario:
                # ########### alterar model do import #########################
                instancia = Salarios(
                    # ######## alterar campos json vs model e chave estrangeira
                    chave_migracao=item['chave_migracao'],
                    funcionario=fk_verdadeira_funcionario,
                    setor=fk_verdadeira_setor,
                    funcao=fk_verdadeira_funcao,
                    data=item['data'],
                    modalidade=item['modalidade'],
                    salario=str(item['salario']),
                    motivo=item['motivo'],
                    comissao_carteira=str(item['comissao_carteira']),
                    comissao_dupla=str(item['comissao_dupla']),
                    comissao_geral=str(item['comissao_geral']),
                    observacoes=item['observacoes'],
                    # ######## usar str() em float ############################
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
