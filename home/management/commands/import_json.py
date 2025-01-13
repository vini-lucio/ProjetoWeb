import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from home.models import EstadosIcms
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_estados

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_uf_origem = get_estados()
estrangeiro_uf_destino = get_estados()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_verdadeira_uf_origem = estrangeiro_uf_origem.filter(chave_migracao=item['uf_origem']).first()
            fk_verdadeira_uf_destino = estrangeiro_uf_destino.filter(chave_migracao=item['uf_destino']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_verdadeira_uf_origem and fk_verdadeira_uf_destino:
                # ########### alterar model do import #########################
                instancia = EstadosIcms(
                    # ######## alterar campos json vs model e chave estrangeira
                    uf_origem=fk_verdadeira_uf_origem,
                    uf_destino=fk_verdadeira_uf_destino,
                    icms=str(item['icms']),
                    icms_frete=str(item['icms_frete']),
                    # ######## usar str() em float ############################
                )
                instancia.full_clean()
                instancia.save()

        self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))


# importar produtos reutilizar para migrar novamente com update/create

# import json
# from pathlib import Path
# from django.core.management.base import BaseCommand
# # ########### alterar model do import #########################################
# from home.models import Produtos
# # ########### alterar/comentar get do import ##################################
# from utils.site_setup import get_unidades

# BASE_DIR = Path(__file__).parent.parent.parent.parent
# origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# # ########### alterar/comentar get ############################################
# estrangeiro_unidade = get_unidades()


# class Command(BaseCommand):
#     help = "Importar JSON para Model"

#     def handle(self, *args, **kwargs):
#         with open(origem, 'r') as arquivo:
#             dados = json.load(arquivo)

#         for item in dados:
#             # ########### alterar/comentar chave estrangeira ##################
#             fk_verdadeira_unidade = estrangeiro_unidade.filter(chave_analysis=item['unidade_analysis']).first()
#             # ########### alterar/comentar chave estrangeira obrigatoria ######
#             if fk_verdadeira_unidade:
#                 # ########### alterar model do import #########################
#                 instancia = Produtos(
#                     # ######## alterar campos json vs model e chave estrangeira
#                     chave_migracao=item['chave_migracao'],
#                     unidade=fk_verdadeira_unidade,
#                     chave_analysis=item['chave_analysis'],
#                     nome=item['nome'],
#                     descricao=item['descricao'],
#                     multiplicidade=str(item['multiplicidade']),
#                     tipo_embalagem=item['tipo_embalagem'],
#                     medida_embalagem_x=str(item['medida_embalagem_x']),
#                     medida_embalagem_y=str(item['medida_embalagem_y']),
#                     quantidade_volume=str(item['quantidade_volume']),
#                     medida_volume_padrao=item['medida_volume_padrao'],
#                     medida_volume_x=str(item['medida_volume_x']),
#                     medida_volume_y=str(item['medida_volume_y']),
#                     medida_volume_z=str(item['medida_volume_z']),
#                     m3_volume=str(item['m3_volume']),
#                     peso_liquido=str(item['peso_liquido']),
#                     peso_bruto=str(item['peso_bruto']),
#                     ean13=None if not item['ean13'] else int(float(item['ean13'])),
#                     status=item['status'],
#                     aditivo_percentual=str(item['aditivo_percentual']),
#                     prioridade=item['prioridade'],
#                     # ######## usar str() em float ############################
#                 )
#                 instancia.full_clean()
#                 instancia.save()

#         self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
