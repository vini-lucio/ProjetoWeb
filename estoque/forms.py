from django import forms
from .models import ProdutosPallets, Pallets, Enderecos


class ProdutosPalletsAlterarForm(forms.ModelForm):
    class Meta:
        model = ProdutosPallets
        fields = ['quantidade', 'fornecedor', 'lote_fornecedor',]
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

            self.fields['endereco'].queryset = Enderecos.objects.filter(  # type:ignore
                tipo_produto=pallet.endereco.tipo_produto,
                status='disponivel'
            ).exclude(**filtro_remover)

            # TODO: sugestão de movimentação de endereço


# TODO: sugerir endereço por prioridade de baixo para cima
# TODO: tratar movimentação de produtos, em caso de só ter um produto, excluir o pallet e disponibilizar posição ao inves de deixar pallet vazio ocupando espaço?
# TODO: remover css alternativo do app de estoque e desabilitar alterações pelo admin????
