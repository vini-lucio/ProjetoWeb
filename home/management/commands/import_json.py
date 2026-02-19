import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from estoque.models import ProdutosPallets
# ########### alterar/comentar get do import ##################################
from estoque.models import Enderecos
from home.models import Produtos, Fornecedores

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
enderecos = Enderecos.objects
produtos = Produtos.objects
fornecedor = Fornecedores.objects


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_produto = produtos.filter(nome=item['produto']).first()
            fk_fornecedor = fornecedor.filter(sigla=item['fornecedor']).first()
            pallet = ProdutosPallets.objects.first().pallet  # type:ignore

            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_produto:
                # ########### alterar model do import incluir #########################
                instancia = ProdutosPallets(
                    # ######## alterar campos json vs model e chave estrangeira
                    pallet=pallet,  # placeholder
                    produto=fk_produto,
                    fornecedor=fk_fornecedor,
                    lote_fornecedor=item['lote_fornecedor'],
                    quantidade=str(item['quantidade']),
                    # ######## usar str() em float ############################
                )
                instancia.full_clean()
                instancia.save()

                # ########### buscar model do import atualizar #########################
                endereco = enderecos.filter(nome=item['nome'], coluna=item['coluna'], altura=item['altura'],).first()
                pallet = instancia.pallet
                if pallet and endereco:
                    pallet.endereco = endereco
                    # pallet.valor_meta = str(round(item['valor_meta'], 2))
                    # pallet.valor_real = str(round(item['valor_real'], 2))
                    # pallet.considerar_total = item['considerar_total']
                    pallet.full_clean()
                    pallet.save()
                    # ######## usar str() em float ############################

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
