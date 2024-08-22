from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from utils.imagens import redimensionar_imagem


LARGURA_IMAGEM_PADRAO_PEQUENO = 70
ALTURA_IMAGEM_PADRAO_PEQUENO = 70

LARGURA_IMAGEM_PADRAO_MEDIO = 210
ALTURA_IMAGEM_PADRAO_MEDIO = 70

LARGURA_IMAGEM_PADRAO_GRANDE = 210
ALTURA_IMAGEM_PADRAO_GRANDE = 160


class HomeLinks(models.Model):
    class Meta:
        verbose_name = 'Home Link'
        verbose_name_plural = 'Home Links'

    tamanhos_botoes = {
        'pequeno': 'Pequeno',
        'medio': 'Medio',
        'grande': 'Grande',
    }

    help_text_imagem_capa = (
        "A imagem será redimensionada automaticamente ao incluir nova imagem "
        "de acordo com o tamanho do botão selecionado: "
        f"Pequeno {LARGURA_IMAGEM_PADRAO_PEQUENO}x{ALTURA_IMAGEM_PADRAO_PEQUENO} px, "
        f"Medio {LARGURA_IMAGEM_PADRAO_MEDIO}x{ALTURA_IMAGEM_PADRAO_MEDIO} px, "
        f"Grande {LARGURA_IMAGEM_PADRAO_GRANDE}x{ALTURA_IMAGEM_PADRAO_GRANDE} px"
    )

    help_text_ordem = "Mudar numero para forçar outra ordenação"

    titulo = models.CharField("Título", max_length=30, unique=True, blank=False, null=False)
    slug = models.SlugField("Slug", unique=True, default='', null=False, blank=True, max_length=255)
    tamanho_botao = models.CharField("Tamanho do Botão", max_length=10, choices=tamanhos_botoes,  # type:ignore
                                     default='grande', blank=False, null=False)  # type:ignore
    imagem_capa = models.ImageField("Imagem de Capa", upload_to='home/link_capa/',
                                    blank=True, default='', help_text=help_text_imagem_capa)
    link_externo = models.BooleanField("Link Externo", blank=False, null=False, default=False)
    url_externo = models.CharField("URL do Link Externo", max_length=2048, blank=True, null=True)
    visivel = models.BooleanField("Visível", blank=False, null=False, default=True)
    conteudo = models.TextField("Conteudo")
    ordem = models.DecimalField("Ordem", max_digits=7, decimal_places=2,
                                default=1000.00, blank=False, null=False, help_text=help_text_ordem)  # type:ignore

    def save(self, *args, **kwargs) -> None:
        if not self.link_externo:
            self.url_externo = ''
        if not self.url_externo and self.link_externo:
            raise ValidationError("Informar URL do Link Externo")

        if not self.slug == slugify(self.titulo):
            self.slug = slugify(self.titulo)

        imagem_capa_anteior = self.imagem_capa.name
        super_save = super().save(*args, **kwargs)

        if self.imagem_capa and self.imagem_capa.name != imagem_capa_anteior:
            largura = 0
            altura = 0

            if self.tamanho_botao == 'pequeno':
                largura = LARGURA_IMAGEM_PADRAO_PEQUENO
                altura = ALTURA_IMAGEM_PADRAO_PEQUENO
            elif self.tamanho_botao == 'medio':
                largura = LARGURA_IMAGEM_PADRAO_MEDIO
                altura = ALTURA_IMAGEM_PADRAO_MEDIO
            elif self.tamanho_botao == 'grande':
                largura = LARGURA_IMAGEM_PADRAO_GRANDE
                altura = ALTURA_IMAGEM_PADRAO_GRANDE

            redimensionar_imagem(self.imagem_capa, largura, altura)

        return super_save

    def __str__(self) -> str:
        return self.titulo
