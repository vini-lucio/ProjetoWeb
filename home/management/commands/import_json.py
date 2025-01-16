import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from frete.models import TransportadorasRegioesValores
# ########### alterar/comentar get do import ##################################
from utils.site_setup import get_transportadoras_origem_destino

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
estrangeiro_transportadora_origem_destino = get_transportadoras_origem_destino()


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_transportadora_origem_destino = estrangeiro_transportadora_origem_destino.filter(
                transportadora__nome=item['transportadora'],
                estado_origem_destino__uf_origem__chave_migracao=item['origem'],
                estado_origem_destino__uf_destino__chave_migracao=item['destino'],
            ).first()
            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_transportadora_origem_destino:
                # ########### alterar model do import #########################
                instancia = TransportadorasRegioesValores(
                    # ######## alterar campos json vs model e chave estrangeira
                    transportadora_origem_destino=fk_transportadora_origem_destino,
                    descricao=item['descricao'],
                    atendimento_cidades_especificas=item['atendimento_cidades_especificas'],
                    status=item['status'],
                    razao=str(item['razao']),
                    advaloren=str(item['advaloren']),
                    advaloren_valor_minimo=str(item['advaloren_valor_minimo']),
                    gris=str(item['gris']),
                    gris_valor_minimo=str(item['gris_valor_minimo']),
                    taxa_coleta=str(item['taxa_coleta']),
                    taxa_conhecimento=str(item['taxa_conhecimento']),
                    taxa_sefaz=str(item['taxa_sefaz']),
                    taxa_suframa=str(item['taxa_suframa']),
                    pedagio_fracao=str(item['pedagio_fracao']),
                    pedagio_valor_fracao=str(item['pedagio_valor_fracao']),
                    pedagio_valor_minimo=str(item['pedagio_valor_minimo']),
                    valor_kg=str(item['valor_kg']),
                    valor_kg_excedente=item['valor_kg_excedente'],
                    taxa_frete_peso=str(item['taxa_frete_peso']),
                    taxa_frete_peso_valor_minimo=str(item['taxa_frete_peso_valor_minimo']),
                    taxa_valor_mercadorias=str(item['taxa_valor_mercadorias']),
                    taxa_valor_mercadorias_valor_minimo=str(item['taxa_valor_mercadorias_valor_minimo']),
                    frete_minimo_valor=str(item['frete_minimo_valor']),
                    frete_minimo_percentual=str(item['frete_minimo_percentual']),
                    observacoes=item['observacoes'],
                    prazo_tipo=item['prazo_tipo'],
                    prazo_padrao=str(item['prazo_padrao']),
                    frequencia_padrao=item['frequencia_padrao'],
                    observacoes_prazo_padrao=item['observacoes_prazo_padrao'],
                    atendimento_zona_rural=item['atendimento_zona_rural'],
                    taxa_zona_rural=str(item['taxa_zona_rural']),
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
