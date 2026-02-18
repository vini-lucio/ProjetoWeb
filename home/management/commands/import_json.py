from django.core.management.base import BaseCommand
from estoque.models import Enderecos, ProdutosTipos


class Command(BaseCommand):
    help = "Incluir endereços para materia prima"

    def handle(self, *args, **kwargs):
        tipo_produto = ProdutosTipos.objects.filter(descricao='MATERIA PRIMA').first()

        nomes = [
            'RUA MP A',
            'RUA MP B',
            'RUA MP C',
            'RUA MP D',
            'RUA MP E',
            'RUA MP F',
            'RUA MP G',
        ]

        colunas = list(range(1, 17))
        alturas = list(range(1, 5))

        for nome in nomes:
            for coluna in colunas:
                # Quantidade total de colunas
                if nome in ['RUA MP A',] and coluna > 13:
                    continue
                if nome in ['RUA MP B', 'RUA MP C', 'RUA MP D', 'RUA MP E',] and coluna > 15:
                    continue
                if nome in ['RUA MP G',] and coluna > 4:
                    continue

                # Colunas sem vão
                if nome in ['RUA MP A', 'RUA MP G',] and coluna in [5, 6]:
                    continue

                for altura in alturas:
                    # Quantidade total de alturas
                    if nome not in ['RUA MP G',] and altura > 3:
                        continue

                    # Vão
                    if nome in ['RUA MP B', 'RUA MP C', 'RUA MP D',
                                'RUA MP E', 'RUA MP F',] and coluna in [5, 6] and altura in [1, 2]:
                        continue

                    instancia = Enderecos(
                        nome=nome,
                        coluna=coluna,
                        altura=altura,
                        tipo='porta_pallet',
                        tipo_produto=tipo_produto,
                        prioridade=1,
                    )
                    instancia.full_clean()
                    instancia.save()

        self.stdout.write(self.style.SUCCESS("Sucesso"))


# import json
# from pathlib import Path
# from django.core.management.base import BaseCommand
# # ########### alterar model do import #########################################
# from dashboards.models import MetasCarteiras
# # ########### alterar/comentar get do import ##################################
# from dashboards.models import IndicadoresValores
# from rh.models import Funcionarios
# from home.models import Vendedores

# BASE_DIR = Path(__file__).parent.parent.parent.parent
# origem = BASE_DIR / '__localcode' / 'migracao' / 'migrar.json'

# # ########### alterar/comentar get ############################################
# indicador_valor = IndicadoresValores.objects
# funcionarios = Funcionarios.objects
# vendedores = Vendedores.objects


# class Command(BaseCommand):
#     help = "Importar JSON para Model"

#     def handle(self, *args, **kwargs):
#         with open(origem, 'r') as arquivo:
#             dados = json.load(arquivo)

#         for item in dados:
#             # ########### alterar/comentar chave estrangeira ##################
#             fk_indicador_valor = indicador_valor.filter(indicador_id=item['indicador_id'],
#                                                         periodo__ano_referencia=item['ano_referencia'],
#                                                         periodo__mes_referencia=item['mes_referencia'],).first()
#             fk_funcionario = funcionarios.filter(pk=item['responsavel_id']).first()
#             fk_vendedor = vendedores.filter(pk=item['vendedor_id']).first()

#             # ########### alterar/comentar chave estrangeira obrigatoria ######
#             if fk_indicador_valor and fk_vendedor:
#                 # ########### alterar model do import incluir #########################
#                 # instancia = MetasCarteiras(
#                 #     # ######## alterar campos json vs model e chave estrangeira
#                 #     # transportadora_regiao_valor=fk_transportadora_regiao_valores,
#                 #     # cidade=fk_cidades,
#                 #     ano_referencia=item['ano_referencia'],
#                 #     mes_referencia=item['mes_referencia'],
#                 #     data_inicio=item['data_inicio'],
#                 #     data_fim=item['data_fim'],
#                 #     primeiro_dia_util=item['primeiro_dia_util'],
#                 #     primeiro_dia_util_proximo_mes=item['primeiro_dia_util_proximo_mes'],
#                 #     dias_uteis_considerar=str(item['dias_uteis_considerar']),
#                 #     dias_uteis_reais=str(item['dias_uteis_reais']),
#                 #     # ######## usar str() em float ############################
#                 # )
#                 # instancia.full_clean()
#                 # instancia.save()

#                 # ########### buscar model do import atualizar #########################
#                 instancia = MetasCarteiras.objects.filter(
#                     indicador_valor=fk_indicador_valor, vendedor=fk_vendedor).first()
#                 if instancia:
#                     instancia.responsavel = fk_funcionario
#                     instancia.valor_meta = str(round(item['valor_meta'], 2))
#                     instancia.valor_real = str(round(item['valor_real'], 2))
#                     instancia.considerar_total = item['considerar_total']
#                     instancia.full_clean()
#                     instancia.save()
#                     # ######## usar str() em float ############################

#         self.stdout.write(self.style.SUCCESS("Dados importados com sucesso"))
