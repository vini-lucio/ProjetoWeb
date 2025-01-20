import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from frete.models import TransportadorasRegioesCidades
# ########### alterar/comentar get do import ##################################
from utils.site_setup import (get_transportadoras_regioes_valores, get_transportadoras, get_estados, get_estados_icms,
                              get_transportadoras_origem_destino, get_cidades)

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_transportadora_regiao_valores = get_transportadoras_regioes_valores()
estrangeiro_cidades = get_cidades()
transportadoras = get_transportadoras()
estados_origem = get_estados()
estados_destino = get_estados()
estados_origem_destino = get_estados_icms()
transportadoras_origem_destino = get_transportadoras_origem_destino()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_transportadora = transportadoras.filter(nome=item['transportadora']).first()
            fk_origem = estados_origem.filter(chave_migracao=item['origem']).first()
            fk_destino = estados_destino.filter(chave_migracao=item['destino']).first()
            fk_origem_destino = estados_origem_destino.filter(uf_origem=fk_origem, uf_destino=fk_destino).first()
            fk_transportadora_origem_destino = transportadoras_origem_destino.filter(
                transportadora=fk_transportadora,
                estado_origem_destino=fk_origem_destino
            ).first()
            fk_transportadora_regiao_valores = estrangeiro_transportadora_regiao_valores.filter(
                transportadora_origem_destino=fk_transportadora_origem_destino,
                descricao=item['descricao'],
            ).first()
            fk_cidades = estrangeiro_cidades.filter(estado=fk_destino, nome=item['cidade']).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_transportadora_regiao_valores and fk_cidades:
                # ########### alterar model do import #########################
                instancia = TransportadorasRegioesCidades(
                    # ######## alterar campos json vs model e chave estrangeira
                    transportadora_regiao_valor=fk_transportadora_regiao_valores,
                    cidade=fk_cidades,
                    prazo_tipo=item['prazo_tipo'],
                    prazo=item['prazo'],
                    frequencia=item['frequencia'],
                    observacoes=item['observacoes'],
                    taxa=str(item['taxa']),
                    cif=item['cif'],
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
