from estoque.models import Enderecos, ProdutosPallets
from home.models import ProdutosTipos
from django.db.models import Count, Sum
from utils.oracle.conectar import executar_oracle
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

            resumo_mp = ProdutosPallets.objects.filter(produto__tipo__descricao='MATERIA PRIMA')
            resumo_mp = resumo_mp.values('produto__nome', 'produto__unidade__unidade')
            resumo_mp = resumo_mp.annotate(quantidade=Sum('quantidade'), pallets=Count('pk')).order_by('-quantidade')

            dt_resumo_mp = pd.DataFrame(resumo_mp)
            dt_resumo_mp = dt_resumo_mp.rename(columns={'produto__nome': 'produto',
                                                        'produto__unidade__unidade': 'unidade'})

            dt_total_mp = pd.DataFrame([dt_resumo_mp[['quantidade', 'pallets']].sum()])

            if com_sugestao:

                # Sugestão de compra de materia prima

                sugestao_mp = producao_por_mp()
                dt_sugestao_mp = pd.DataFrame(sugestao_mp)
                dt_sugestao_mp = dt_sugestao_mp.rename(columns={'MATERIA_PRIMA': 'produto',
                                                                'MEDIA_MES': 'media_mes_prod',
                                                                'UNIDADE': 'unidade', })
                total_produzido_mp = dt_sugestao_mp['media_mes_prod'].sum()
                dt_sugestao_mp['proporcao_mes_prod'] = dt_sugestao_mp['media_mes_prod'] / total_produzido_mp
                dt_sugestao_mp['sugestao_ocupar'] = (self.enderecos_totais_mp[0].get(
                    'quantidade_total') - self.enderecos_totais_mp[0].get(  # type:ignore
                    'quantidade_ocupada')) * dt_sugestao_mp['proporcao_mes_prod']  # type:ignore
                dt_sugestao_mp['sugestao_ocupar'] = (dt_sugestao_mp['sugestao_ocupar']).where(
                    (dt_sugestao_mp['sugestao_ocupar'] > 1) & (dt_sugestao_mp['sugestao_ocupar'] != 0), 1)
                dt_sugestao_mp['sugestao_ocupar'] = dt_sugestao_mp['sugestao_ocupar'].apply(math.floor)

                # Resumo + Sugestão

                dt_resumo_mp = pd.merge(dt_resumo_mp, dt_sugestao_mp, 'outer', ['produto', 'unidade']).fillna(0)

            # Final

            self.resumo_mp = dt_resumo_mp.to_dict(orient='records')
            self.total_mp = dt_total_mp.to_dict(orient='records')[0] if not dt_total_mp.empty else None


def producao_por_mp():
    """Retorna a quantidade por materia prima dos prodtos proprios embalados nos ultimos 365 dias."""
    sql = """
        SELECT MATERIA_PRIMA.MATERIA_PRIMA,
            ROUND(
                SUM(
                    APONTAMENTOS.PRODUCAO_LIQUIDA * PRODUTOS.PESO_LIQUIDO
                ) / 12,
                3
            ) AS MEDIA_MES,
            MATERIA_PRIMA.UNIDADE
        FROM (
                SELECT PROCESSOS_MATERIAIS.CHAVE_PROCESSO,
                    PRODUTOS.CODIGO AS MATERIA_PRIMA,
                    PROCESSOS_MATERIAIS.QUANTIDADE,
                    UNIDADES.UNIDADE
                FROM COPLAS.UNIDADES,
                    COPLAS.PROCESSOS_MATERIAIS,
                    COPLAS.PRODUTOS
                WHERE PRODUTOS.CPROD = PROCESSOS_MATERIAIS.CHAVE_MATERIAL
                    AND UNIDADES.CHAVE = PRODUTOS.CHAVE_UNIDADE
                    AND PRODUTOS.CHAVE_GRUPO = 8273
            ) MATERIA_PRIMA,
            COPLAS.PRODUTOS,
            COPLAS.PROCESSOS_OPERACOES,
            COPLAS.PROCESSOS,
            COPLAS.APONTAMENTOS,
            COPLAS.ORDENS
        WHERE ORDENS.CHAVE = APONTAMENTOS.CHAVE_ORDEM
            AND ORDENS.CHAVE_PROCESSO = PROCESSOS.CHAVE
            AND PROCESSOS_OPERACOES.CHAVE_PROCESSO = PROCESSOS.CHAVE
            AND PRODUTOS.CPROD = ORDENS.CHAVE_PRODUTO
            AND MATERIA_PRIMA.CHAVE_PROCESSO = PROCESSOS.CHAVE
            AND APONTAMENTOS.CHAVE_SETOR = 12
            AND PROCESSOS_OPERACOES.CHAVE_SETOR = 12
            AND PRODUTOS.CHAVE_FAMILIA = 7766
            AND APONTAMENTOS.INICIO >= SYSDATE - 365
        GROUP BY MATERIA_PRIMA.MATERIA_PRIMA,
            MATERIA_PRIMA.UNIDADE
    """

    resultado = executar_oracle(sql, exportar_cabecalho=True)

    return resultado
