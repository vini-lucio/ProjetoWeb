import json
from pathlib import Path
from django.core.management.base import BaseCommand
# ########### alterar model do import #########################################
from dashboards.models import MetasCarteiras
# ########### alterar/comentar get do import ##################################
from dashboards.models import IndicadoresValores
from rh.models import Funcionarios
from home.models import Vendedores

BASE_DIR = Path(__file__).parent.parent.parent.parent
origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# ########### alterar/comentar get ############################################
indicador_valor = IndicadoresValores.objects
funcionarios = Funcionarios.objects
vendedores = Vendedores.objects


class Command(BaseCommand):
    help = "Importar JSON para Model"

    def handle(self, *args, **kwargs):
        with open(origem, 'r') as arquivo:
            dados = json.load(arquivo)

        for item in dados:
            # ########### alterar/comentar chave estrangeira ##################
            fk_indicador_valor = indicador_valor.filter(indicador_id=item['indicador_id'],
                                                        periodo__ano_referencia=item['ano_referencia'],
                                                        periodo__mes_referencia=item['mes_referencia'],).first()
            fk_funcionario = funcionarios.filter(pk=item['responsavel_id']).first()
            fk_vendedor = vendedores.filter(pk=item['vendedor_id']).first()

            # ########### alterar/comentar chave estrangeira obrigatoria ######
            if fk_indicador_valor and fk_vendedor:
                # ########### alterar model do import incluir #########################
                # instancia = MetasCarteiras(
                #     # ######## alterar campos json vs model e chave estrangeira
                #     # transportadora_regiao_valor=fk_transportadora_regiao_valores,
                #     # cidade=fk_cidades,
                #     ano_referencia=item['ano_referencia'],
                #     mes_referencia=item['mes_referencia'],
                #     data_inicio=item['data_inicio'],
                #     data_fim=item['data_fim'],
                #     primeiro_dia_util=item['primeiro_dia_util'],
                #     primeiro_dia_util_proximo_mes=item['primeiro_dia_util_proximo_mes'],
                #     dias_uteis_considerar=str(item['dias_uteis_considerar']),
                #     dias_uteis_reais=str(item['dias_uteis_reais']),
                #     # ######## usar str() em float ############################
                # )
                # instancia.full_clean()
                # instancia.save()

                # ########### buscar model do import atualizar #########################
                instancia = MetasCarteiras.objects.filter(
                    indicador_valor=fk_indicador_valor, vendedor=fk_vendedor).first()
                if instancia:
                    instancia.responsavel = fk_funcionario
                    instancia.valor_meta = str(round(item['valor_meta'], 2))
                    instancia.valor_real = str(round(item['valor_real'], 2))
                    instancia.considerar_total = item['considerar_total']
                    instancia.full_clean()
                    instancia.save()
                    # ######## usar str() em float ############################

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
