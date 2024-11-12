import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from rh.models import Dependentes
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_funcionarios, get_dependentes_tipos

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_funcionario = get_funcionarios()
estrangeiro_dependente_tipo = get_dependentes_tipos()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_funcionario = estrangeiro_funcionario.filter(chave_migracao=item['funcionario']).first()
            fk_verdadeira_dependente_tipo = estrangeiro_dependente_tipo.filter(
                chave_migracao=item['dependente_tipo']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_funcionario:
                # ########### alterar model do import #########################
                instancia = Dependentes(
                    # ######## alterar campos json vs model e chave estrangeira
                    # ######## usar str() em float ############################
                    chave_migracao=item['chave_migracao'],
                    funcionario=fk_verdadeira_funcionario,
                    dependente_tipo=fk_verdadeira_dependente_tipo,
                    nome=item['nome'],
                    data_nascimento=item['data_nascimento'],
                    rg=item['rg'],
                    cpf=item['cpf'],
                    dependente_ir=item['dependente_ir'],
                    certidao_tipo=item['certidao_tipo'],
                    certidao_data_emissao=item['certidao_data_emissao'],
                    certidao_termo_matricula=item['certidao_termo_matricula'],
                    certidao_livro=item['certidao_livro'],
                    certidao_folha=item['certidao_folha'],
                    observacoes=item['observacoes'],
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
