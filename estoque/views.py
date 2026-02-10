from typing import Dict
from analysis.models import OC_MP_ITENS
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.db.models.functions import Concat
from .models import ProdutosPallets, Enderecos
from .forms import (ProdutosPalletsAlterarForm, PalletsMoverForm, ProdutosPalletsMoverForm, ProdutosPalletsExcluirForm,
                    ProdutosPalletsIncluirLoteMPForm)
from utils.base_forms import FormPesquisarMixIn


def estoque(request):
    """Retorna pagina de estoque"""
    titulo_pagina = 'Estoque'

    contexto: Dict = {'titulo_pagina': titulo_pagina, }

    formulario = FormPesquisarMixIn()

    if request.method == 'GET' and request.GET:
        formulario = FormPesquisarMixIn(request.GET)
        dados = []

        if formulario.is_valid():
            pesquisar = formulario.cleaned_data.get('pesquisar')
            dados = ProdutosPallets.objects.annotate(
                fornecedor_lote=Concat('fornecedor__sigla', 'lote_fornecedor')).filter(
                Q(produto__nome__icontains=pesquisar) |
                Q(pallet__endereco__nome__icontains=pesquisar) |
                Q(fornecedor_lote__icontains=pesquisar)
            )

        contexto.update({'dados': dados, })

    contexto.update({'formulario': formulario, })

    return render(request, 'estoque/pages/estoque.html', contexto)


@user_passes_test(lambda usuario: usuario.has_perm('estoque.change_produtospallets'), login_url='/admin/login/')
def estoque_alterar(request, pk: int):
    """Retorna pagina de alteração de produto no estoque"""
    produto_pallet = get_object_or_404(ProdutosPallets, pk=pk)
    pallet = produto_pallet.pallet
    produto = produto_pallet.produto
    endereco = pallet.endereco

    titulo_pagina = 'Alterar'

    # busca paremetro da url enviado na pagina de estoque para lembrar o filtro da pesquisa
    url_destino = request.GET.get('destino', reverse('estoque:estoque'))

    formulario = ProdutosPalletsAlterarForm(instance=produto_pallet)
    formulario_excluir = ProdutosPalletsExcluirForm(pallet=pallet)
    if request.method == 'POST' and request.POST:
        formulario = ProdutosPalletsAlterarForm(request.POST, instance=produto_pallet)
        formulario_excluir = ProdutosPalletsExcluirForm(request.POST, pallet=pallet)

        if 'salvar-submit' in request.POST:
            if formulario.is_valid():
                formulario.save()
                return redirect(url_destino)

        if 'excluir-submit' in request.POST:
            if formulario_excluir.is_valid():
                acao = formulario_excluir.cleaned_data.get('acao')
                if acao == 'disponibilizar':
                    produto_pallet.delete(disponibilizar_endereco=True)
                else:
                    produto_pallet.delete(disponibilizar_endereco=False)
                return redirect(url_destino)

    contexto: Dict = {'titulo_pagina': titulo_pagina, 'produto_pallet': produto_pallet, 'formulario': formulario,
                      'url_destino': url_destino, 'pallet': pallet, 'endereco': endereco,
                      'produto': produto, 'formulario_excluir': formulario_excluir, }

    return render(request, 'estoque/pages/estoque-alterar.html', contexto)


@user_passes_test(lambda usuario: usuario.has_perm('estoque.change_produtospallets'), login_url='/admin/login/')
def estoque_mover(request, pk: int):
    """Retorna pagina de alteração de produto no estoque"""
    produto_pallet = get_object_or_404(ProdutosPallets, pk=pk)
    pallet = produto_pallet.pallet
    produto = produto_pallet.produto
    endereco = pallet.endereco

    titulo_pagina = 'Mover'

    # busca paremetro da url enviado na pagina de estoque para lembrar o filtro da pesquisa
    url_destino = request.GET.get('destino', reverse('estoque:estoque'))

    formulario_mover_pallet = PalletsMoverForm(instance=pallet)
    formulario_mover_mesmo_produto_pallet = ProdutosPalletsMoverForm(mesmo_produto=True, instance=produto_pallet)
    formulario_mover_diferente_produto_pallet = ProdutosPalletsMoverForm(mesmo_produto=False, instance=produto_pallet)
    formulario_excluir = ProdutosPalletsExcluirForm(pallet=pallet)

    if request.method == 'POST' and request.POST:
        formulario_mover_pallet = PalletsMoverForm(request.POST, instance=pallet)
        formulario_mover_mesmo_produto_pallet = ProdutosPalletsMoverForm(request.POST, mesmo_produto=True,
                                                                         instance=produto_pallet)
        formulario_mover_diferente_produto_pallet = ProdutosPalletsMoverForm(request.POST, mesmo_produto=False,
                                                                             instance=produto_pallet)
        formulario_excluir = ProdutosPalletsExcluirForm(request.POST, pallet=pallet)

        if 'salvar-submit' in request.POST:
            if formulario_mover_pallet.is_valid():
                formulario_mover_pallet.save()
                return redirect(url_destino)

        if 'expedicao-picking-submit' in request.POST:
            destino = Enderecos.objects.get(nome='Expedição')
            if endereco.tipo_produto.descricao == "MATERIA PRIMA":
                destino = Enderecos.objects.get(nome='Picking Produção')

            pallet.endereco = destino
            pallet.full_clean()
            pallet.save()
            return redirect(url_destino)

        if 'salvar-mesmo-produto-submit' in request.POST:
            if formulario_mover_mesmo_produto_pallet.is_valid():
                formulario_mover_mesmo_produto_pallet.save()
                return redirect(url_destino)

        if 'salvar-produto-diferente-submit' in request.POST:
            if formulario_mover_diferente_produto_pallet.is_valid():
                formulario_mover_diferente_produto_pallet.save()
                return redirect(url_destino)

        if 'excluir-submit' in request.POST:
            if formulario_excluir.is_valid():
                acao = formulario_excluir.cleaned_data.get('acao')
                if acao == 'disponibilizar':
                    produto_pallet.delete(disponibilizar_endereco=True)
                else:
                    produto_pallet.delete(disponibilizar_endereco=False)
                return redirect(url_destino)

    contexto: Dict = {'titulo_pagina': titulo_pagina, 'pallet': pallet,
                      'formulario_mover_pallet': formulario_mover_pallet,
                      'formulario_mover_mesmo_produto_pallet': formulario_mover_mesmo_produto_pallet,
                      'formulario_mover_diferente_produto_pallet': formulario_mover_diferente_produto_pallet,
                      'url_destino': url_destino, 'produto': produto, 'produto_pallet': produto_pallet,
                      'endereco': endereco, 'formulario_excluir': formulario_excluir, }

    return render(request, 'estoque/pages/estoque-mover.html', contexto)


@user_passes_test(lambda usuario: usuario.has_perm('estoque.change_produtospallets'), login_url='/admin/login/')
def estoque_incluir_lote_mp(request, pk: int):
    """Retorna pagina de inclusão de lote de recebimento de materia prima"""
    item_oc = get_object_or_404(OC_MP_ITENS, CHAVE=pk)

    titulo_pagina = 'Incluir Lote de MP'

    # busca paremetro da url enviado na pagina de estoque para lembrar o filtro da pesquisa
    url_destino = request.GET.get('destino', reverse('estoque:estoque'))

    formulario_incluir_lote_mp = ProdutosPalletsIncluirLoteMPForm(item_oc=item_oc)

    if request.method == 'POST' and request.POST:
        formulario_incluir_lote_mp = ProdutosPalletsIncluirLoteMPForm(request.POST, item_oc=item_oc)

        if formulario_incluir_lote_mp.is_valid():
            formulario_incluir_lote_mp.incluir_lote_mp()
            return redirect(url_destino)

    contexto: Dict = {'titulo_pagina': titulo_pagina, 'url_destino': url_destino, 'item_oc': item_oc,
                      'formulario_incluir_lote_mp': formulario_incluir_lote_mp, }

    return render(request, 'estoque/pages/estoque-incluir-lote-mp.html', contexto)
