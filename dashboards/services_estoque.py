from estoque.models import Enderecos
from home.models import ProdutosTipos
from django.db.models import Count
import pandas as pd


class DashBoardEstoque():
    """Gera dashboard de estoque."""

    def __init__(self) -> None:
        self.embalagem = Enderecos.objects.filter(nome='Embalagem').first()
        self.expedicao = Enderecos.objects.filter(nome='Expedição').first()
        self.picking_producao = Enderecos.objects.filter(nome='Picking Produção').first()
        self.recebimento = Enderecos.objects.filter(nome='Recebimento').first()

        produto_acabado = ProdutosTipos.objects.filter(descricao='PRODUTO ACABADO').first()
        materia_prima = ProdutosTipos.objects.filter(descricao='MATERIA PRIMA').first()

        self.ocupado_vazio_produto_acabado = Enderecos.quantidade_enderecos_vazios_ocupados(
            produto_acabado)  # type:ignore
        self.ocupado_vazio_mp = Enderecos.quantidade_enderecos_vazios_ocupados(materia_prima)  # type:ignore

        enderecos_validos = Enderecos.objects.exclude(tipo='chao')
        enderecos_ocupados = enderecos_validos.filter(status__in=['ocupado', 'reservado'])

        quantidade_enderecos_validos = enderecos_validos.values(
            'tipo', 'tipo_produto__descricao').annotate(quantidade=Count('pk'))
        for enderecos in quantidade_enderecos_validos:
            # Substituir coluna tipo pelo valor em choices
            enderecos['tipo'] = Enderecos.tipos.get(enderecos['tipo'])

        quantidade_enderecos_ocupados = enderecos_ocupados.values(
            'tipo', 'tipo_produto__descricao').annotate(quantidade=Count('pk'))
        for enderecos in quantidade_enderecos_ocupados:
            # Substituir coluna tipo pelo valor em choices
            enderecos['tipo'] = Enderecos.tipos.get(enderecos['tipo'])

        quantidade_enderecos_validos = pd.DataFrame(quantidade_enderecos_validos)
        quantidade_enderecos_validos = quantidade_enderecos_validos.rename(
            columns={'quantidade': 'quantidade_total', 'tipo_produto__descricao': 'tipo_produto'})

        quantidade_enderecos_ocupados = pd.DataFrame(quantidade_enderecos_ocupados)
        quantidade_enderecos_ocupados = quantidade_enderecos_ocupados.rename(
            columns={'quantidade': 'quantidade_ocupada', 'tipo_produto__descricao': 'tipo_produto'})

        if not quantidade_enderecos_validos.empty and not quantidade_enderecos_ocupados.empty:
            enderecos = pd.merge(quantidade_enderecos_validos, quantidade_enderecos_ocupados,
                                 'left', ['tipo', 'tipo_produto']).fillna(0)
        else:
            enderecos = quantidade_enderecos_validos.copy()
            enderecos['quantidade_ocupada'] = 0

        if not quantidade_enderecos_validos.empty:
            enderecos['quantidade_disponivel'] = enderecos['quantidade_total'] - enderecos['quantidade_ocupada']

            # Ocupação endereços de produto acabado

            self.enderecos_produto_acabado = enderecos[enderecos['tipo_produto'] == 'PRODUTO ACABADO'].copy()
            self.enderecos_totais_produto_acabado = pd.DataFrame(
                [self.enderecos_produto_acabado[['quantidade_total', 'quantidade_ocupada']].sum()])

            self.enderecos_produto_acabado['ocupacao'] = self.enderecos_produto_acabado['quantidade_ocupada'] / \
                self.enderecos_produto_acabado['quantidade_total'] * 100
            self.enderecos_totais_produto_acabado['ocupacao'] = self.enderecos_totais_produto_acabado['quantidade_ocupada'] / \
                self.enderecos_totais_produto_acabado['quantidade_total'] * 100

            self.enderecos_produto_acabado = self.enderecos_produto_acabado.to_dict(orient='records')
            self.enderecos_totais_produto_acabado = self.enderecos_totais_produto_acabado.to_dict(orient='records')

            # Ocupação endereços de materia prima

            self.enderecos_mp = enderecos[enderecos['tipo_produto'] != 'PRODUTO ACABADO'].copy()
            self.enderecos_totais_mp = pd.DataFrame(
                [self.enderecos_mp[['quantidade_total', 'quantidade_ocupada']].sum()])

            self.enderecos_mp['ocupacao'] = self.enderecos_mp['quantidade_ocupada'] / \
                self.enderecos_mp['quantidade_total'] * 100
            self.enderecos_totais_mp['ocupacao'] = self.enderecos_totais_mp['quantidade_ocupada'] / \
                self.enderecos_totais_mp['quantidade_total'] * 100

            self.enderecos_mp = self.enderecos_mp.to_dict(orient='records')
            self.enderecos_totais_mp = self.enderecos_totais_mp.to_dict(orient='records')
