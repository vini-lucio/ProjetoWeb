from django.db import models
from django.utils.text import slugify
from utils.imagens import redimensionar_imagem
from django_summernote.models import AbstractAttachment
from django.db.models import Q, Max
from utils.base_models import BaseLogModel
from utils.converter import converter_data_django_para_str_ddmmyyyy, converter_data_django_para_dia_semana
from utils.choices import status_ativo_inativo
from utils.conferir_alteracao import campo_django_mudou


class PostAttachment(AbstractAttachment):
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name

        nome_arquivo_atual = str(self.file.name)
        super_save = super().save(*args, **kwargs)

        if self.file and nome_arquivo_atual != self.file.name:
            redimensionar_imagem(self.file)

        return super_save


FATOR_AMPLIACAO_HOVER_CSS = 1.05

LARGURA_IMAGEM_PADRAO_PEQUENO = round(70 * FATOR_AMPLIACAO_HOVER_CSS)
ALTURA_IMAGEM_PADRAO_PEQUENO = round(70 * FATOR_AMPLIACAO_HOVER_CSS)

LARGURA_IMAGEM_PADRAO_MEDIO = round(210 * FATOR_AMPLIACAO_HOVER_CSS)
ALTURA_IMAGEM_PADRAO_MEDIO = round(70 * FATOR_AMPLIACAO_HOVER_CSS)

LARGURA_IMAGEM_PADRAO_GRANDE = round(210 * FATOR_AMPLIACAO_HOVER_CSS)
ALTURA_IMAGEM_PADRAO_GRANDE = round(160 * FATOR_AMPLIACAO_HOVER_CSS)


class HomeLinks(models.Model):
    class Meta:
        verbose_name = 'Home Link'
        verbose_name_plural = 'Home Links'
        constraints = [
            models.UniqueConstraint(
                fields=['titulo',],
                name='homelinks_unique_titulo',
                violation_error_message="Titulo é campo unico"
            ),
            models.UniqueConstraint(
                fields=['slug',],
                name='homelinks_unique_slug',
                violation_error_message="Slug é campo unico"
            ),
            models.CheckConstraint(
                check=(Q(link_externo=True) & Q(url_externo__isnull=False)) | Q(link_externo=False),
                name='homelinks_check_url_externo',
                violation_error_message="Informar URL do Link Externo"
            ),
        ]

    tamanhos_botoes = {
        'pequeno': 'Pequeno',
        'medio': 'Medio',
        'grande': 'Grande',
        'comunicado': 'Comunicado',
        'consultoria': 'Consultoria de Vendas',
    }

    help_text_tamanho_botao = "Se alterar esse campo, inclua a imagem novamente para redimensionar"

    help_text_imagem_capa = (
        "Tamanho 'Consultoria de Vendas' e 'Comunicado' não exibe imagem de capa, deixar em branco. "
        "A imagem será redimensionada automaticamente ao incluir nova imagem "
        "de acordo com o tamanho do botão selecionado: "
        f"Pequeno {LARGURA_IMAGEM_PADRAO_PEQUENO}x{ALTURA_IMAGEM_PADRAO_PEQUENO} px, "
        f"Medio {LARGURA_IMAGEM_PADRAO_MEDIO}x{ALTURA_IMAGEM_PADRAO_MEDIO} px, "
        f"Grande {LARGURA_IMAGEM_PADRAO_GRANDE}x{ALTURA_IMAGEM_PADRAO_GRANDE} px"
    )

    help_text_ordem = "Mudar numero para forçar outra ordenação"

    titulo = models.CharField("Título", max_length=30, blank=False, null=False)
    slug = models.SlugField("Slug", default='', null=False, blank=True, max_length=255)
    tamanho_botao = models.CharField("Tamanho do Botão", max_length=30, choices=tamanhos_botoes,  # type:ignore
                                     default='grande', blank=False, null=False,
                                     help_text=help_text_tamanho_botao)  # type:ignore
    imagem_capa = models.ImageField("Imagem de Capa", upload_to='home/link_capa/%Y/%m/',
                                    blank=True, default='', help_text=help_text_imagem_capa)
    link_externo = models.BooleanField("Link Externo", blank=False, null=False, default=False)
    url_externo = models.CharField("URL do Link Externo", max_length=2048, blank=True, null=True)
    visivel = models.BooleanField("Visível", blank=False, null=False, default=True)
    conteudo = models.TextField("Conteudo", blank=True, null=True)
    ordem = models.DecimalField("Ordem", max_digits=7, decimal_places=2,
                                default=1000.00, blank=False, null=False, help_text=help_text_ordem)  # type:ignore

    def clean(self):
        if not self.link_externo:
            self.url_externo = ''
        return super().clean()

    def save(self, *args, **kwargs) -> None:
        if not self.slug == slugify(self.titulo):
            self.slug = slugify(self.titulo)

        imagem_capa_anteior = self.imagem_capa.name
        super_save = super().save(*args, **kwargs)

        if self.imagem_capa and self.imagem_capa.name != imagem_capa_anteior:
            largura = None
            altura = None

            if self.tamanho_botao == 'pequeno':
                largura = LARGURA_IMAGEM_PADRAO_PEQUENO
                altura = ALTURA_IMAGEM_PADRAO_PEQUENO
            elif self.tamanho_botao == 'medio':
                largura = LARGURA_IMAGEM_PADRAO_MEDIO
                altura = ALTURA_IMAGEM_PADRAO_MEDIO
            elif self.tamanho_botao == 'grande':
                largura = LARGURA_IMAGEM_PADRAO_GRANDE
                altura = ALTURA_IMAGEM_PADRAO_GRANDE

            # tamanho imagem comunicado é none, largura maxima de 1200px, somente otimizar
            redimensionar_imagem(self.imagem_capa, largura, altura)

        return super_save

    def __str__(self) -> str:
        return self.titulo


class HomeLinksDocumentos(models.Model):
    class Meta:
        verbose_name = 'Documento Home Link'
        verbose_name_plural = 'Documentos Home Link'
        ordering = 'nome',
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'home_link',],
                name='homelinksdocumentos_unique_nome',
                violation_error_message="Nome é campo unico dentro de um Home Link"
            ),
        ]

    home_link = models.ForeignKey(HomeLinks, verbose_name="Home Link", on_delete=models.CASCADE,
                                  related_name="%(class)s")
    nome = models.CharField("Nome Documento", max_length=50)
    documento = models.FileField("Documento", upload_to='home/link_documento/%Y/%m/')

    def __str__(self) -> str:
        return self.nome


class SiteSetup(models.Model):
    class Meta:
        verbose_name = "Site Setup"
        verbose_name_plural = "Site Setup"

    help_text_favicon = "A imagem será redimensionada para 32x32 px"
    help_text_logo = "A imagem será redimensionada proporcionalmente para 100 px de altura"

    favicon = models.ImageField("Favicon", upload_to='home/favicon/%Y/%m/', blank=True,
                                null=True, help_text=help_text_favicon)
    logo_cabecalho = models.ImageField("Logo", upload_to='home/logo/%Y/%m/',
                                       blank=True, null=True, help_text=help_text_logo)
    texto_rodape = models.TextField("Texto do Rodapé", blank=True, null=True)
    primeiro_dia_mes = models.DateField("Primeiro Dia do Mês", default='2000-01-01',  # type:ignore
                                        auto_now=False, auto_now_add=False)
    primeiro_dia_util_mes = models.DateField("Primeiro Dia Util do Mês", default='2000-01-01',  # type:ignore
                                             auto_now=False, auto_now_add=False)
    ultimo_dia_mes = models.DateField("Ultimo Dia do Mês", default='2000-01-01',  # type:ignore
                                      auto_now=False, auto_now_add=False)
    primeiro_dia_util_proximo_mes = models.DateField("Primeiro Dia Util do Proximo Mês",
                                                     default='2000-01-01',  # type:ignore
                                                     auto_now=False, auto_now_add=False)
    meta_mes = models.DecimalField("Meta do Mês", default=0.00, max_digits=15, decimal_places=2)  # type:ignore
    dias_uteis_mes = models.DecimalField("Dias Uteis no Mês", default=0.00,  # type:ignore
                                         max_digits=5, decimal_places=2)
    meta_diaria = models.DecimalField("Meta Diaria", default=0.00, max_digits=15, decimal_places=2)  # type:ignore
    despesa_administrativa_fixa = models.DecimalField("Despesa Administrativa Fixa %", default=0.00,  # type:ignore
                                                      max_digits=5, decimal_places=2)
    rentabilidade_verde = models.DecimalField("Rentabilidade Verde %", default=0.00,   # type:ignore
                                              max_digits=5, decimal_places=2)
    rentabilidade_amarela = models.DecimalField("Rentabilidade Amarela %", default=0.00,  # type:ignore
                                                max_digits=5, decimal_places=2)
    rentabilidade_vermelha = models.DecimalField("Rentabilidade Vermelha %", default=0.00,  # type:ignore
                                                 max_digits=5, decimal_places=2)
    atualizacoes_ano = models.IntegerField("Ano", default=2000)
    atualizacoes_ano_inicio = models.IntegerField("Ano Inicio", default=2000)
    atualizacoes_ano_fim = models.IntegerField("Ano Fim", default=2001)
    atualizacoes_data_ano_inicio = models.DateField("Data Ano Inicio", default='2000-01-01',  # type:ignore
                                                    auto_now=False, auto_now_add=False)
    atualizacoes_data_ano_fim = models.DateField("Data Ano Fim", default='2000-12-31',  # type:ignore
                                                 auto_now=False, auto_now_add=False)
    atualizacoes_mes = models.IntegerField("Mês", default=1)
    atualizacoes_data_mes_inicio = models.DateField("Data Mês Inicio", default='2000-01-01',  # type:ignore
                                                    auto_now=False, auto_now_add=False)
    atualizacoes_data_mes_fim = models.DateField("Data Mês Fim", default='2000-01-31',  # type:ignore
                                                 auto_now=False, auto_now_add=False)
    medida_volume_padrao_x = models.DecimalField("Medida Volume Padrão X (m)", max_digits=5, decimal_places=2,
                                                 default=0)  # type:ignore
    medida_volume_padrao_y = models.DecimalField("Medida Volume Padrão Y (m)", max_digits=5, decimal_places=2,
                                                 default=0)  # type:ignore
    medida_volume_padrao_z = models.DecimalField("Medida Volume Padrão Z (m)", max_digits=5, decimal_places=2,
                                                 default=0)  # type:ignore

    @property
    def primeiro_dia_mes_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.primeiro_dia_mes)

    @property
    def primeiro_dia_util_mes_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.primeiro_dia_util_mes)

    @property
    def ultimo_dia_mes_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.ultimo_dia_mes)

    @property
    def primeiro_dia_util_proximo_mes_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.primeiro_dia_util_proximo_mes)

    @property
    def atualizacoes_data_ano_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.atualizacoes_data_ano_inicio)

    @property
    def atualizacoes_data_ano_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.atualizacoes_data_ano_fim)

    @property
    def atualizacoes_data_mes_inicio_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.atualizacoes_data_mes_inicio)

    @property
    def atualizacoes_data_mes_fim_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.atualizacoes_data_mes_fim)

    @property
    def meta_mes_as_float(self):
        return float(self.meta_mes)

    @property
    def dias_uteis_mes_as_float(self):
        return float(self.dias_uteis_mes)

    @property
    def meta_diaria_as_float(self):
        return float(self.meta_diaria)

    @property
    def despesa_administrativa_fixa_as_float(self):
        return float(self.despesa_administrativa_fixa)

    @property
    def rentabilidade_verde_as_float(self):
        return float(self.rentabilidade_verde)

    @property
    def rentabilidade_amarela_as_float(self):
        return float(self.rentabilidade_amarela)

    @property
    def rentabilidade_vermelha_as_float(self):
        return float(self.rentabilidade_vermelha)

    def clean(self) -> None:
        if self.dias_uteis_mes == 0:
            self.meta_diaria = 0
        else:
            self.meta_diaria = self.meta_mes / self.dias_uteis_mes
        return super().clean()

    def save(self, *args, **kwargs) -> None:
        favicon_anterior = self.favicon.name
        logo_cabecalho_anterior = self.logo_cabecalho.name

        medida_volume_padrao_mudou = campo_django_mudou(SiteSetup, self,
                                                        medida_volume_padrao_x=self.medida_volume_padrao_x,
                                                        medida_volume_padrao_y=self.medida_volume_padrao_y,
                                                        medida_volume_padrao_z=self.medida_volume_padrao_z)

        super_save = super().save(*args, **kwargs)

        if self.favicon and self.favicon.name != favicon_anterior:
            largura = 32
            altura = 32
            redimensionar_imagem(self.favicon, largura, altura)

        if self.logo_cabecalho and self.logo_cabecalho.name != logo_cabecalho_anterior:
            largura = None
            altura = 100
            redimensionar_imagem(self.logo_cabecalho, largura, altura)

        if medida_volume_padrao_mudou:
            produtos_volume_padrao = Produtos.objects.filter(medida_volume_padrao=True)
            for produto in produtos_volume_padrao:
                produto.medida_volume_x = self.medida_volume_padrao_x
                produto.medida_volume_y = self.medida_volume_padrao_y
                produto.medida_volume_z = self.medida_volume_padrao_z
                produto.full_clean()
                produto.save()

        return super_save

    def __str__(self) -> str:
        return "Site Setup"


class AssistentesTecnicos(models.Model):
    class Meta:
        verbose_name = 'Assistente Tecnico'
        verbose_name_plural = 'Assistentes Tecnicos'
        constraints = [
            models.UniqueConstraint(
                fields=['nome',],
                name='assistente_unique_nome',
                violation_error_message="Nome é campo unico"
            ),
        ]

    status_assitentes = status_ativo_inativo

    nome = models.CharField("Nome", max_length=30)
    status = models.CharField("Status", max_length=30, choices=status_assitentes, default='ativo')  # type:ignore

    def __str__(self) -> str:
        return self.nome


class AssistentesTecnicosAgenda(models.Model):
    class Meta:
        verbose_name = 'Agenda VEC'
        verbose_name_plural = 'Agenda VEC'
        ordering = '-data',
        constraints = [
            models.UniqueConstraint(
                fields=['data', 'assistente_tecnico',],
                name='agenda_unique_data_assistente',
                violation_error_message="Assistente Tecnico e Data são unicos dentro da agenda"
            ),
        ]

    data = models.DateField("Data", auto_now=False, auto_now_add=False)
    assistente_tecnico = models.ForeignKey(AssistentesTecnicos, verbose_name="Assistente Tecnico",
                                           on_delete=models.PROTECT, related_name="%(class)s")
    agenda = models.CharField("Agenda", max_length=50)

    @property
    def data_as_ddmmyyyy(self):
        return converter_data_django_para_str_ddmmyyyy(self.data)

    data_as_ddmmyyyy.fget.short_description = 'Data'  # type:ignore

    @property
    def data_dia_semana(self):
        return converter_data_django_para_dia_semana(self.data)

    data_dia_semana.fget.short_description = 'Dia da Semana'  # type:ignore

    def __str__(self) -> str:
        return f'{self.data_as_ddmmyyyy} - {self.assistente_tecnico}'


class Jobs(models.Model):
    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='jobs_unique_descricao',
                violation_error_message="Descrição é unica em Jobs"
            ),
        ]

    status_jobs = status_ativo_inativo

    descricao = models.CharField("Descrição", max_length=30)
    razao_social = models.CharField("Razão Social", max_length=100, null=True, blank=True)
    cnpj = models.CharField("CNPJ", max_length=20, null=True, blank=True)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)
    status = models.CharField("Status", max_length=30, choices=status_jobs, default='ativo')  # type:ignore

    def __str__(self) -> str:
        return self.descricao


class Paises(models.Model):
    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        constraints = [
            models.UniqueConstraint(
                fields=['nome',],
                name='paises_unique_nome',
                violation_error_message="Nome é unico em Países"
            ),
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='paises_unique_chave_analysis',
                violation_error_message="Chave Analysis é unico em Países"
            ),
        ]

    chave_analysis = models.IntegerField("ID Analysis")
    nome = models.CharField("Nome", max_length=30)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.nome


class Estados(models.Model):
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        constraints = [
            models.UniqueConstraint(
                fields=['uf',],
                name='estados_unique_uf',
                violation_error_message="UF é unico em Estados"
            ),
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='estados_unique_chave_analysis',
                violation_error_message="Chave Analysis é unico em Estados"
            ),
            models.UniqueConstraint(
                fields=['sigla',],
                name='estados_unique_sigla',
                violation_error_message="Sigla é unico em Estados"
            ),
        ]

    chave_analysis = models.IntegerField("ID Analysis")
    uf = models.CharField("UF", max_length=30)
    sigla = models.CharField("Sigla", max_length=2)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return self.uf


class Cidades(models.Model):
    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        constraints = [
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='cidades_unique_chave_analysis',
                violation_error_message="Chave Analysis é unico em Cidades"
            ),
        ]

    chave_analysis = models.IntegerField("ID Analysis")
    estado = models.ForeignKey(Estados, verbose_name="Estado", on_delete=models.PROTECT, related_name="%(class)s")
    nome = models.CharField("Nome", max_length=70)
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.nome} - {self.estado.sigla}'


class Bancos(models.Model):
    class Meta:
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'
        constraints = [
            models.UniqueConstraint(
                fields=['nome',],
                name='bancos_unique_nome',
                violation_error_message="Nome é unico em Banco"
            ),
        ]

    nome = models.CharField("Nome", max_length=50)

    def __str__(self) -> str:
        return self.nome


class Atualizacoes(models.Model):
    class Meta:
        verbose_name = 'Atualização'
        verbose_name_plural = 'Atualizações'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='atualizacoes_unique_descricao',
                violation_error_message="Descrição é campo unico"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=100)
    nome_funcao = models.CharField("Nome Função", max_length=200)
    observacoes = models.CharField("Observações", max_length=300, blank=True, null=True)

    def __str__(self) -> str:
        return self.descricao


class ProdutosModelosTags(models.Model):
    class Meta:
        verbose_name = 'Produtos Modelos Tag'
        verbose_name_plural = 'Produtos Modelos Tags'
        ordering = 'descricao',
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='tags_unique_descricao',
                violation_error_message="Descrição é campo unico"
            ),
        ]

    descricao = models.CharField("Descrição", max_length=100)
    slug = models.SlugField("Slug", blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.slug == slugify(self.descricao):
            self.slug = slugify(self.descricao)

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.descricao


class ProdutosModelos(BaseLogModel):
    class Meta:
        verbose_name = 'Produtos Modelo'
        verbose_name_plural = 'Produtos Modelos'
        constraints = [
            models.UniqueConstraint(
                fields=['descricao',],
                name='modelos_unique_descricao',
                violation_error_message="Descrição é campo unico"
            ),
        ]

    help_text_imagem = "A imagem será redimensionada proporcionalmente para 300 px de largura"

    descricao = models.CharField("Descrição", max_length=100)
    imagem = models.ImageField("Imagem Principal", upload_to='home/produtos_modelos/%Y/%m/', blank=True, null=True,
                               help_text=help_text_imagem)
    tags = models.ManyToManyField(ProdutosModelosTags, verbose_name="Tags", related_name="%(class)s", blank=True,
                                  default='')
    slug = models.SlugField("Slug", blank=True, null=True)
    url_site = models.CharField("URL do Site", max_length=2048, blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.slug == slugify(self.descricao):
            self.slug = slugify(self.descricao)

        imagem_anterior = self.imagem.name

        super_save = super().save(*args, **kwargs)

        if self.imagem and self.imagem.name != imagem_anterior:
            largura = 300
            altura = None
            redimensionar_imagem(self.imagem, largura, altura)

        return super_save

    def __str__(self) -> str:
        return self.descricao


class ProdutosModelosTopicos(BaseLogModel):
    class Meta:
        verbose_name = 'Produtos Modelos Topico'
        verbose_name_plural = 'Produtos Modelos Topicos'
        ordering = 'ordem',

    modelo = models.ForeignKey(ProdutosModelos, verbose_name="Modelo", on_delete=models.PROTECT,
                               related_name="%(class)s")
    titulo = models.CharField("Titulo", max_length=100)
    conteudo = models.TextField("Conteudo")
    ordem = models.IntegerField("Ordem", default=10)

    def save(self, *args, **kwargs) -> None:
        if not self.pk:
            modelo = ProdutosModelosTopicos.objects.filter(modelo=self.modelo)
            ultima_ordem = modelo.aggregate(Max('ordem'))['ordem__max']
            if ultima_ordem:
                self.ordem = ultima_ordem + 10
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.titulo


class Unidades(models.Model):
    class Meta:
        verbose_name = 'Unidade'
        verbose_name_plural = 'Unidades'
        constraints = [
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='unidades_unique_chave_analysis',
                violation_error_message="Chave Analysis é unico em Unidades"
            ),
            models.UniqueConstraint(
                fields=['unidade',],
                name='unidades_unique_unidade',
                violation_error_message="Unidade é unico em Unidades"
            ),
        ]

    chave_analysis = models.IntegerField("ID Analysis")
    unidade = models.CharField("Unidade", max_length=6)
    descricao = models.CharField("Descrição", max_length=20)

    def __str__(self) -> str:
        return f'{self.descricao}'


class Produtos(BaseLogModel):
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        constraints = [
            models.UniqueConstraint(
                fields=['chave_analysis',],
                name='produtos_unique_chave_analysis',
                violation_error_message="Chave Analysis é campo unico"
            ),
            models.UniqueConstraint(
                fields=['nome',],
                name='produtos_unique_nome',
                violation_error_message="Nome é campo unico"
            ),
            models.CheckConstraint(
                check=Q(multiplicidade__gte=0),
                name='produtos_check_multiplicidade',
                violation_error_message="Multiplicidade precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(medida_embalagem_x__gte=0),
                name='produtos_check_medida_embalagem_x',
                violation_error_message="Medida Embalagem X precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(medida_embalagem_y__gte=0),
                name='produtos_check_medida_embalagem_y',
                violation_error_message="Medida Embalagem Y precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(quantidade_volume__gte=0),
                name='produtos_check_quantidade_volume',
                violation_error_message="Quantidade por Volume precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(medida_volume_x__gte=0),
                name='produtos_check_medida_volume_x',
                violation_error_message="Medida Volume X precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(medida_volume_y__gte=0),
                name='produtos_check_medida_volume_y',
                violation_error_message="Medida Volume Y precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(medida_volume_z__gte=0),
                name='produtos_check_medida_volume_z',
                violation_error_message="Medida Volume Z precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(m3_volume__gte=0),
                name='produtos_check_m3_volume',
                violation_error_message="m³ do Volume precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(aditivo_percentual__gte=0),
                name='produtos_check_aditivo_percentual_0',
                violation_error_message="Aditivo Percentual precisa ser maior ou igual a 0"
            ),
            models.CheckConstraint(
                check=Q(aditivo_percentual__lte=100),
                name='produtos_check_aditivo_percentual_100',
                violation_error_message="Aditivo Percentual precisa ser menor ou igual a 100"
            ),
            models.CheckConstraint(
                check=Q(prioridade__gte=0),
                name='produtos_check_prioridade',
                violation_error_message="Prioridade precisa ser maior ou igual a 0"
            ),
        ]

    tipos_embalagem = {
        'PLASTICO': 'Plastico',
        'RAFIA': 'Rafia',
        'OUTROS': 'Outros',
    }

    status_produtos = status_ativo_inativo

    help_text_medida_volume_padrao = "Ao marcar esse campo será preenchido as medidas do volume de acordo com o definido em Site Setup"

    chave_analysis = models.IntegerField("ID Analysis")
    modelo = models.ForeignKey(ProdutosModelos, verbose_name="Modelo", on_delete=models.PROTECT,
                               related_name="%(class)s", null=True, blank=True)
    unidade = models.ForeignKey(Unidades, verbose_name="Unidade", on_delete=models.PROTECT, related_name="%(class)s")
    nome = models.CharField("Nome", max_length=70)
    descricao = models.CharField("Descrição", max_length=100)
    multiplicidade = models.DecimalField("Multiplicidade", max_digits=8, decimal_places=4, default=0)  # type:ignore
    tipo_embalagem = models.CharField("Tipo Embalagem", max_length=20, null=True, blank=True,
                                      choices=tipos_embalagem)  # type:ignore
    medida_embalagem_x = models.DecimalField("Medida Embalagem X (m)", max_digits=5, decimal_places=2,
                                             default=0)  # type:ignore
    medida_embalagem_y = models.DecimalField("Medida Embalagem Y (m)", max_digits=5, decimal_places=2,
                                             default=0)  # type:ignore
    quantidade_volume = models.DecimalField("Quantidade Por Volume", max_digits=10, decimal_places=4,
                                            default=0)  # type:ignore
    medida_volume_padrao = models.BooleanField("Medida Volume Padrão", default=False,
                                               help_text=help_text_medida_volume_padrao)
    medida_volume_x = models.DecimalField("Medida Volume X (m)", max_digits=5, decimal_places=2,
                                          default=0)  # type:ignore
    medida_volume_y = models.DecimalField("Medida Volume Y (m)", max_digits=5, decimal_places=2,
                                          default=0)  # type:ignore
    medida_volume_z = models.DecimalField("Medida Volume Z (m)", max_digits=5, decimal_places=2,
                                          default=0)  # type:ignore
    m3_volume = models.DecimalField("m³ do Volume", max_digits=7, decimal_places=4, default=0)  # type:ignore
    peso_liquido = models.DecimalField("Peso Liquido (kg)", max_digits=8, decimal_places=4, default=0)  # type:ignore
    peso_bruto = models.DecimalField("Peso Bruto (kg)", max_digits=8, decimal_places=4, default=0)  # type:ignore
    ean13 = models.CharField("Codigo de Barras EAN13", max_length=13, null=True, blank=True)
    status = models.CharField("Status", max_length=10, default='ativo', choices=status_produtos)  # type:ignore
    aditivo_percentual = models.DecimalField("% Aditivo (cor)", max_digits=5, decimal_places=2,
                                             default=0)  # type:ignore
    prioridade = models.DecimalField("Prioridade", max_digits=4, decimal_places=0, default=0)  # type:ignore
    chave_migracao = models.IntegerField("Chave Migração", null=True, blank=True)

    def save(self, *args, **kwargs) -> None:
        if self.medida_volume_padrao:
            site_setup = SiteSetup.objects.first()
            if site_setup:
                self.medida_volume_x = site_setup.medida_volume_padrao_x
                self.medida_volume_y = site_setup.medida_volume_padrao_y
                self.medida_volume_z = site_setup.medida_volume_padrao_z

        self.m3_volume = self.medida_volume_x * self.medida_volume_y * self.medida_volume_z

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nome
