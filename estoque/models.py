from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from home.models import Produtos, Fornecedores, ProdutosTipos


class Enderecos(models.Model):
    class Meta:
        verbose_name = 'Endereço Estoque'
        verbose_name_plural = 'Endereços Estoque'
        ordering = 'nome', 'coluna', '-altura',
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'coluna', 'altura'],
                name='enderecos_unique_endereco',
                violation_error_message="Nome, Coluna e Altura são campos unicos"
            ),
        ]

    tipos = {
        'pilha_rack': 'Pilha de Rack',
        'porta_pallet': 'Porta Pallet',
        'prateleira': 'Prateleira',
        'chao': 'Chão',
    }

    status_enderecos = {
        'disponivel': 'Disponivel',
        'ocupado': 'Ocupado',
        'reservado': 'Reservado',
        'inativo': 'Inativo',
    }

    nome = models.CharField("Nome", max_length=50)
    coluna = models.IntegerField("Coluna", default=0)
    altura = models.IntegerField("Altura", default=0)
    tipo = models.CharField("Tipo", max_length=20, choices=tipos)  # type:ignore
    tipo_produto = models.ForeignKey(ProdutosTipos, verbose_name="Tipo de Produto", on_delete=models.PROTECT,
                                     related_name="%(class)s")
    prioridade = models.IntegerField("Prioridade", default=0)
    multi_pallet = models.BooleanField("Multi Pallet", default=False)
    status = models.CharField("Status", max_length=20, default='disponivel', choices=status_enderecos)  # type:ignore

    def clean(self) -> None:
        """Valida se Endereços Multi Pallet possuem Tipo Chão. Valida se Endereços Tipo Chão possuem Coluna e Altura
        igual a 0. Valida se Endereços Tipo diferente de Chão possuem Coluna e Altura maior que 0."""
        super_clean = super().clean()

        if self.multi_pallet and self.tipo != 'chao':
            raise ValidationError({'multi_pallet': "Multi Pallet precisa ter tipo Chão"})

        if self.tipo == 'chao' and (self.coluna != 0 or self.altura != 0):
            raise ValidationError({'coluna': "Coluna precisa ser 0 quando tipo Chão",
                                   'altura': "Altura precisa ser 0 quando tipo Chão"})

        if self.tipo != 'chao' and (self.coluna == 0 or self.altura == 0):
            raise ValidationError({'coluna': "Coluna precisa maior que 0 quando tipo não for Chão",
                                   'altura': "Altura precisa maior que 0 quando tipo não for Chão"})

        return super_clean

    def ocupar(self):
        """Ocupa o endereço que não é multi pallet"""
        if self.multi_pallet:
            return
        self.status = 'ocupado'
        self.full_clean()
        self.save()

    def disponibilizar(self):
        """Disponibiliza o endereço. Se endereço for tipo pilha, os endereços ocupados acima descem 1 altura."""
        self.status = 'disponivel'
        self.full_clean()
        self.save()

        # "Cair a pilha"
        if self.tipo == 'pilha_rack':
            altura_acima = self.altura + 1
            endereco_acima = Enderecos.objects.filter(nome=self.nome, coluna=self.coluna, altura=altura_acima).first()
            if not endereco_acima:
                return

            pallet_acima = Pallets.objects.filter(endereco=endereco_acima).first()
            if not pallet_acima:
                return

            pallet_acima.endereco = self
            pallet_acima.full_clean()
            pallet_acima.save()

    def __str__(self) -> str:
        return f'{self.nome}, Col.: {self.coluna}, Alt.: {self.altura} - {self.status}'


class Pallets(models.Model):
    class Meta:
        verbose_name = 'Pallet'
        verbose_name_plural = 'Pallets'
        constraints = [
            models.CheckConstraint(
                check=Q(quantidade_produtos__gte=0),
                name='pallets_check_quantidade_produtos',
                violation_error_message="Quantidade de Produtos precisa ser maior ou igual a 0"
            ),
        ]

    endereco = models.ForeignKey(Enderecos, verbose_name="Endereço", on_delete=models.PROTECT,
                                 related_name="%(class)s")
    quantidade_produtos = models.IntegerField("Quantidade de Produtos", default=0)

    def incluir_produto(self):
        """Soma 1 na quantidade de produtos"""
        self.quantidade_produtos += 1
        self.full_clean()
        self.save()

    def remover_produto(self):
        """Subtrai 1 na quantidade de produtos. Quando endereço é tipo chão o Pallet é excluido se nova quantidade for 0."""
        self.quantidade_produtos -= 1
        self.full_clean()
        self.save()

        if self.endereco.tipo == 'chao' and self.quantidade_produtos == 0:
            self.delete()

    def delete(self, *args, **kwargs):
        """Disponiliza o endereço."""
        super_delete = super().delete(*args, **kwargs)

        self.endereco.disponibilizar()

        return super_delete

    def clean(self) -> None:
        """Valida se novo endereço está com status disponivel. Valida se endereço atual e endereço novo possuem
        o mesmo tipo de produto. Valida endereço novo, quando tipo for pilha de racks, se endereço abaixo está ocupado."""
        super_clean = super().clean()

        if self.pk:
            pallet_atual = Pallets.objects.get(pk=self.pk)
            endereco_atual = pallet_atual.endereco
            endereco_novo = self.endereco

            # Validações movimentação de pallets
            if endereco_atual != endereco_novo:
                if endereco_novo.status != 'disponivel':
                    raise ValidationError({'endereco': "Endereço não disponivel"})
                if endereco_novo.tipo == 'pilha_rack' and endereco_novo.altura > 1:
                    altura_abaixo = endereco_novo.altura - 1
                    endereco_novo_abaixo = Enderecos.objects.filter(nome=endereco_novo.nome,
                                                                    coluna=endereco_novo.coluna,
                                                                    altura=altura_abaixo).first()
                    if not endereco_novo_abaixo.pallets.exists():  # type:ignore
                        raise ValidationError({'endereco': "Endereço de tipo pilha precisa ter altura abaixo ocupada"})
                if endereco_atual.tipo_produto != endereco_novo.tipo_produto:
                    raise ValidationError({'endereco': "Endereço de tipo de produto diferente"})

        return super_clean

    def save(self, *args, **kwargs) -> None:
        """Ocupa e disponibiliza os endereços e quando um Pallet sem produtos move para um endereço tipo chão, ele é
        excluido"""
        endereco_atual = None
        endereco_novo = None
        if self.pk:
            pallet_atual = Pallets.objects.get(pk=self.pk)
            endereco_atual = pallet_atual.endereco
            endereco_novo = self.endereco

        super_save = super().save(*args, **kwargs)

        # Atualização do status do endereço
        if endereco_atual != endereco_novo:
            endereco_novo.ocupar()  # type:ignore
            endereco_atual.disponibilizar()  # type:ignore

            if endereco_novo.tipo == 'chao' and not self.produtospallets.exists():  # type:ignore
                self.delete()

        return super_save

    def __str__(self) -> str:
        return f'{self.pk} - {self.endereco}'


class ProdutosPallets(models.Model):
    # TODO: criar chave estrangeira com embalagem, guardar tipo de embalagem
    class Meta:
        verbose_name = 'Produto Pallet'
        verbose_name_plural = 'Produtos Pallet'
        constraints = [
            models.CheckConstraint(
                check=Q(quantidade__gt=0),
                name='produtospallets_check_quantidade',
                violation_error_message="Quantidade precisa ser maior que 0"
            ),
        ]

    pallet = models.ForeignKey(Pallets, verbose_name="Pallet", on_delete=models.PROTECT, related_name="%(class)s")
    produto = models.ForeignKey(Produtos, verbose_name="Produto", on_delete=models.PROTECT, related_name="%(class)s")
    quantidade = models.DecimalField("Quantidade", max_digits=14, decimal_places=4, default=0)  # type:ignore
    fornecedor = models.ForeignKey(Fornecedores, verbose_name="Fornecedor", on_delete=models.PROTECT,
                                   related_name="%(class)s", null=True, blank=True)
    lote_fornecedor = models.CharField("Lote Fornecedor", max_length=50, null=True, blank=True)

    @property
    def unidade(self):
        return self.produto.unidade.unidade

    unidade.fget.short_description = 'Unidade'  # type:ignore

    @property
    def endereco(self):
        return self.pallet.endereco.nome

    endereco.fget.short_description = 'Endereço'  # type:ignore

    @property
    def endereco_coluna(self):
        return self.pallet.endereco.coluna

    endereco_coluna.fget.short_description = 'Coluna'  # type:ignore

    @property
    def endereco_altura(self):
        return self.pallet.endereco.altura

    endereco_altura.fget.short_description = 'Altura'  # type:ignore

    def __str__(self) -> str:
        return f'{self.pallet} - {self.produto} - {self.quantidade} {self.unidade}'

    def delete(self, *args, **kwargs):
        """Atualiza a quantidade de produtos no pallet."""
        super_delete = super().delete(*args, **kwargs)

        self.pallet.remover_produto()

        return super_delete

    def save(self, *args, **kwargs):
        """Se for um novo registro, um pallet é criado automaticamente no endereço de recebimento (se produto for
        tipo materia prima) ou embalagem (se produto não for tipo materia prima).

        Na alteração de pallet do produto, se o produto não existe no pallet destino ele é movido e a quantidade de
        itens é atualiza nos dois pallets. Se o produto já existir no pallet destino, ele é excluido da origem e sua
        quantidade é somada ao destino."""

        # Inclusão
        if not self.pk:
            if self.produto:
                if self.produto.tipo.descricao == 'MATERIA PRIMA':  # type:ignore
                    novo_endereco = Enderecos.objects.filter(nome='Recebimento', coluna=0, altura=0).first()
                else:
                    novo_endereco = Enderecos.objects.filter(nome='Embalagem', coluna=0, altura=0).first()

                novo_pallet = Pallets.objects.create(endereco=novo_endereco, quantidade_produtos=1)
                novo_pallet.full_clean()
                novo_pallet.save()

                self.pallet = novo_pallet

            return super().save(*args, **kwargs)

        # Alteração
        pallet_atual = None
        pallet_novo = None
        pallet_novo_contem_mesmo_produto = None
        if self.pk:
            produto_pallet_atual = ProdutosPallets.objects.get(pk=self.pk)
            pallet_atual = produto_pallet_atual.pallet
            pallet_novo = self.pallet

            if pallet_atual != pallet_novo:
                pallet_novo_contem_mesmo_produto = pallet_novo.produtospallets.filter(  # type:ignore
                    produto=self.produto).first()

        if not pallet_novo_contem_mesmo_produto:
            super().save(*args, **kwargs)

            # Atualização da quantidade de produtos no pallet
            if pallet_atual != pallet_novo:
                pallet_novo.incluir_produto()  # type:ignore
                pallet_atual.remover_produto()  # type:ignore
        else:
            pallet_novo_contem_mesmo_produto.quantidade += self.quantidade
            pallet_novo_contem_mesmo_produto.full_clean()
            pallet_novo_contem_mesmo_produto.save()
            self.delete()
