from django import forms
from analysis.models import OC_MP_ITENS
from .models import ProdutosPallets, Pallets, Enderecos
import math


class ProdutosPalletsAlterarForm(forms.ModelForm):
    class Meta:
        model = ProdutosPallets
        fields = ['quantidade', 'fornecedor', 'lote_fornecedor', 'aprovado',]
        widgets = {
            'quantidade': forms.NumberInput(attrs={'style': 'width: 19rem;'}),
            'lote_fornecedor': forms.TextInput(attrs={'style': 'width: 19rem;'}),
        }

    def __init__(self, *args, **kwargs):
        """Atualiza campos dependendo do tipo de produto"""
        super().__init__(*args, **kwargs)

        produto_pallet = self.instance
        if produto_pallet.pk:
            if produto_pallet.produto.tipo.descricao == 'PRODUTO ACABADO':
                self.fields.pop('fornecedor', None)
                self.fields.pop('lote_fornecedor', None)


class ProdutosPalletsMoverForm(forms.ModelForm):
    class Meta:
        model = ProdutosPallets
        fields = ['pallet',]

    def __init__(self, *args, mesmo_produto: bool, **kwargs):
        """Filtra lista de pallets em endereços de mesmo tipo de produto e se os pallets possuem ou não o mesmo
        produto do pallet movido.

        Parametros:
        -----------
        :mesmo_produto (bool): se a listagem é com o mesmo produto ou não.
        """
        super().__init__(*args, **kwargs)

        produto_pallet = self.instance

        if produto_pallet.pk:
            # filtro para lista de pallets
            produto = produto_pallet.produto
            pallet = produto_pallet.pallet

            filtro_remover = {}
            if pallet.endereco.tipo_produto.descricao == 'PRODUTO ACABADO':
                filtro_remover = {'endereco__tipo': 'porta_pallet'}
                if pallet.tipo_embalagem_produto == 'RAFIA':
                    filtro_remover = {'endereco__tipo': 'pilha_rack'}

            if mesmo_produto:
                queryset = Pallets.objects.filter(produtospallets__produto=produto).exclude(pk=pallet.pk)
            else:
                queryset = Pallets.objects.filter(
                    endereco__tipo_produto=pallet.endereco.tipo_produto
                ).exclude(produtospallets__produto=produto).exclude(**filtro_remover)

            self.fields['pallet'].queryset = queryset  # type:ignore


class ProdutosPalletsExcluirForm(forms.Form):
    acao = forms.ChoiceField(label="Ação", choices=[])

    def __init__(self, *args, pallet: Pallets, **kwargs):
        """Atualiza escolhas baseado na quantidade de produtos no pallet.

        Parametros:
        -----------
        :pallet (Pallet, obrigatorio): com o pallet
        """
        super().__init__(*args, **kwargs)

        disponibilizar = {
            '': '--------',
            'nao_disponibilizar': 'Excluir e manter ocupado o endereço',
        }

        if pallet.quantidade_produtos == 1:
            disponibilizar.update({'disponibilizar': 'Excluir e disponibilizar o endereço', })

        self.fields['acao'].choices = disponibilizar  # type:ignore
        self.fields['acao'].initial = ''


class ProdutosPalletsIncluirLoteMPForm(forms.Form):
    quantidade_pallets = forms.IntegerField(label="Qtd. de Pallets*")
    quantidade_por_pallet = forms.DecimalField(label="Qtd. por Pallet", max_digits=22, decimal_places=6, initial=1000)
    lote = forms.CharField(label="Lote / nº NF", max_length=50)

    def __init__(self, *args, item_oc: OC_MP_ITENS, **kwargs):
        """Sugere quantidades de pallets acordo com a quantidade do item de ordem de compra informado.

        Parametros:
        -----------
        :item_oc (OC_MP_ITENS, obrigatorio): com o item de ordem de compra
        """
        super().__init__(*args, **kwargs)

        self.item_oc = item_oc
        self.fields['quantidade_pallets'].initial = math.ceil(self.item_oc.QUANTIDADE / 1000)  # type:ignore

    def incluir_lote_mp(self):
        """Inclui o informado no formulario em Produtos Pallets. Por segurança, a quantidade de pallets a serem
        incluidos não passará de 20."""
        quantidade_pallets = self.cleaned_data.get('quantidade_pallets')
        if quantidade_pallets > 20:  # type:ignore
            quantidade_pallets = 20
        quantidade_por_pallet = self.cleaned_data.get('quantidade_por_pallet')
        lote = self.cleaned_data.get('lote')

        analysis_produto = self.item_oc.CHAVE_MATERIAL  # type:ignore
        analysis_fornecedor = self.item_oc.CHAVE_OC.CHAVE_FORNECEDOR  # type:ignore

        produto = analysis_produto.get_produto()  # type:ignore
        fornecedor = analysis_fornecedor.get_fornecedor()  # type:ignore

        if quantidade_pallets and quantidade_por_pallet:
            for pallet in range(quantidade_pallets):  # type:ignore
                instancia = ProdutosPallets.objects.create(
                    produto=produto,
                    quantidade=quantidade_por_pallet,
                    fornecedor=fornecedor,
                    lote_fornecedor=lote,
                )
                instancia.full_clean()
                instancia.save()


class PalletsMoverForm(forms.ModelForm):
    class Meta:
        model = Pallets
        fields = ['endereco',]

    def __init__(self, *args, **kwargs):
        """Filtra lista de endereços baseado no tipo de embalagem do produto de enderecos de tipo de produto
        PRODUTO ACABADO, somente endereços disponiveis e de mesmo tipo de produto. Sugestão de movimentação
        de endereço baseado na prioridade do produto e disponibilidade de endereço de baixo para cima."""
        super().__init__(*args, **kwargs)

        pallet = self.instance

        if pallet.pk:
            # filtro para lista de endereços
            filtro_remover = {}
            if pallet.endereco.tipo_produto.descricao == 'PRODUTO ACABADO':
                filtro_remover = {'tipo': 'porta_pallet'}
                if pallet.tipo_embalagem_produto == 'RAFIA':
                    filtro_remover = {'tipo': 'pilha_rack'}

            lista_enderecos = Enderecos.objects.filter(tipo_produto=pallet.endereco.tipo_produto,
                                                       status='disponivel').exclude(**filtro_remover)

            self.fields['endereco'].queryset = lista_enderecos.order_by('nome', 'coluna', 'altura')  # type:ignore

            if not self.is_bound:
                sugestao_endereco = lista_enderecos.filter(
                    multi_pallet=False, prioridade__gte=pallet.prioridade
                ).order_by('prioridade', 'altura', 'coluna').first()
                self.initial['endereco'] = sugestao_endereco
