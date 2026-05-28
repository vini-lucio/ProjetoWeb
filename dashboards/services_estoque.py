from analysis.models import OC_MP_ITENS
from estoque.models import Enderecos, ProdutosPallets
from home.models import ProdutosTipos
from .services_producao import get_relatorios_producao
from django.db.models import Count, Sum, Q, F
from utils.data_hora_atual import data_365_dias_atras
import math
import pandas as pd


class DashBoardEstoque():
    """Gera dashboard de estoque."""

    def __init__(self, com_sugestao: bool = False) -> None:
        """
        Parametros:
        -----------
        :com_sugestao (bool, default False): se será calculado a sugestao
        """
        self.embalagem = Enderecos.objects.filter(nome='Embalagem').first()
        self.expedicao = Enderecos.objects.filter(nome='Expedição').first()
        self.picking_producao = Enderecos.objects.filter(nome='Picking Produção').first()
        self.recebimento = Enderecos.objects.filter(nome='Recebimento').first()

        produto_acabado = ProdutosTipos.objects.filter(descricao='PRODUTO ACABADO').first()
        materia_prima = ProdutosTipos.objects.filter(descricao='MATERIA PRIMA').first()

        self.ocupado_vazio_produto_acabado = Enderecos.quantidade_enderecos_vazios_ocupados(
            produto_acabado)  # type:ignore
        self.ocupado_vazio_mp = Enderecos.quantidade_enderecos_vazios_ocupados(materia_prima)  # type:ignore

        enderecos_validos = Enderecos.objects.exclude(tipo='chao').exclude(status='inativo').exclude(prioridade=0)
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
            self.enderecos_totais_produto_acabado['ocupacao'] = (self.enderecos_totais_produto_acabado['quantidade_ocupada'] /
                                                                 self.enderecos_totais_produto_acabado['quantidade_total'] * 100).fillna(0)

            self.enderecos_produto_acabado = self.enderecos_produto_acabado.to_dict(orient='records')
            self.enderecos_totais_produto_acabado = self.enderecos_totais_produto_acabado.to_dict(orient='records')

            # Ocupação endereços de materia prima

            self.enderecos_mp = enderecos[enderecos['tipo_produto'] != 'PRODUTO ACABADO'].copy()
            self.enderecos_totais_mp = pd.DataFrame(
                [self.enderecos_mp[['quantidade_total', 'quantidade_ocupada']].sum()])

            self.enderecos_mp['ocupacao'] = self.enderecos_mp['quantidade_ocupada'] / \
                self.enderecos_mp['quantidade_total'] * 100
            self.enderecos_totais_mp['ocupacao'] = (self.enderecos_totais_mp['quantidade_ocupada'] /
                                                    self.enderecos_totais_mp['quantidade_total'] * 100).fillna(0)

            self.enderecos_mp = self.enderecos_mp.to_dict(orient='records')
            self.enderecos_totais_mp = self.enderecos_totais_mp.to_dict(orient='records')

            # Relatorio resumo de quantidade por materia prima

            resumo_mp = ProdutosPallets.objects.filter(produto__tipo__descricao='MATERIA PRIMA').exclude(
                pallet__endereco=self.picking_producao
            ).exclude(Q(pallet__endereco__prioridade=0) & ~Q(pallet__endereco__tipo='chao'))
            resumo_mp = resumo_mp.values('produto__nome', 'produto__unidade__unidade')
            resumo_mp = resumo_mp.annotate(quantidade=Sum('quantidade'), pallets=Count('pk')).order_by('-quantidade')

            dt_resumo_mp = pd.DataFrame(resumo_mp)
            dt_resumo_mp = dt_resumo_mp.rename(columns={'produto__nome': 'produto',
                                                        'produto__unidade__unidade': 'unidade'})
            dt_total_mp = pd.DataFrame([dt_resumo_mp[['quantidade', 'pallets']].sum()])

            if com_sugestao:

                # Sugestão de compra de materia prima

                saldo_rr = list(OC_MP_ITENS.objects.filter(SALDO__gt=0, CHAVE_MATERIAL__CHAVE_GRUPO__pk=8273).values(
                    PRODUTO=F('CHAVE_MATERIAL__CODIGO'), UNIDADE=F('CHAVE_MATERIAL__CHAVE_UNIDADE__UNIDADE'),
                ).annotate(SALDO=Sum(F('SALDO'))).order_by('PRODUTO'))
                dt_saldo_rr = pd.DataFrame(saldo_rr)
                dt_saldo_rr['SALDO'] = pd.to_numeric(dt_saldo_rr['SALDO'], errors='coerce',)
                dt_saldo_rr = dt_saldo_rr.rename(columns={'PRODUTO': 'produto',
                                                          'SALDO': 'saldo_rr', 'UNIDADE': 'unidade', })
                dt_saldo_rr['saldo_rr_pallets'] = (dt_saldo_rr['saldo_rr'] / 1000).apply(math.ceil)

                recebimento = ProdutosPallets.objects.filter(pallet__endereco=self.recebimento)
                recebimento = recebimento.values('produto__nome')
                recebimento = recebimento.annotate(recebimento_pallets=Count('pk'))

                dt_recebimento = pd.DataFrame(recebimento)
                dt_recebimento = dt_recebimento.rename(columns={'produto__nome': 'produto'})

                producao_mp = get_relatorios_producao(data_apontamento_inicio_maior_igual=data_365_dias_atras(),
                                                      coluna_material=True, coluna_quantidade_material_liquido=True,
                                                      coluna_unidade_material=True, setor=12, familia_produto=7766,
                                                      grupo_material=8273,)
                dt_producao_mp = pd.DataFrame(producao_mp)
                dt_producao_mp['QUANTIDADE_MATERIAL_LIQUIDO'] = dt_producao_mp['QUANTIDADE_MATERIAL_LIQUIDO'] / 12
                dt_producao_mp = dt_producao_mp.rename(columns={'MATERIAL': 'produto',
                                                                'QUANTIDADE_MATERIAL_LIQUIDO': 'media_mes_prod',
                                                                'UNIDADE_MATERIAL': 'unidade', })
                total_produzido_mp = dt_producao_mp['media_mes_prod'].sum()
                dt_producao_mp['proporcao_mes_prod'] = dt_producao_mp['media_mes_prod'] / total_produzido_mp

                # Resumo + RR + Sugestão

                dt_resumo_mp = pd.merge(dt_resumo_mp, dt_producao_mp, 'outer', ['produto', 'unidade']).fillna(0)
                dt_resumo_mp = pd.merge(dt_resumo_mp, dt_saldo_rr, 'outer', ['produto', 'unidade']).fillna(0)
                dt_resumo_mp = pd.merge(dt_resumo_mp, dt_recebimento, 'outer', 'produto').fillna(0)
                dt_resumo_mp['sugestao_ocupar'] = (self.enderecos_totais_mp[0].get(
                    'quantidade_total') - self.enderecos_totais_mp[0].get(  # type:ignore
                    'quantidade_ocupada')) * dt_resumo_mp['proporcao_mes_prod']
                dt_resumo_mp['sugestao_ocupar'] = dt_resumo_mp['sugestao_ocupar'] - \
                    dt_resumo_mp['saldo_rr_pallets'] - dt_resumo_mp['recebimento_pallets']
                dt_resumo_mp['sugestao_ocupar'] = (dt_resumo_mp['sugestao_ocupar']).where(
                    (dt_resumo_mp['sugestao_ocupar'] > 1) | (dt_resumo_mp['sugestao_ocupar'] <= 0), 1)
                dt_resumo_mp['sugestao_ocupar'] = dt_resumo_mp['sugestao_ocupar'].apply(math.floor)

            # Final

            self.resumo_mp = dt_resumo_mp.to_dict(orient='records')
            self.total_mp = dt_total_mp.to_dict(orient='records')[0] if not dt_total_mp.empty else None
