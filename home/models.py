from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class HomeLinks(models.Model):
    class Meta:
        verbose_name = 'Home Link'
        verbose_name_plural = 'Home Links'

    tamanhos_botoes = {
        'pequeno': 'Pequeno',
        'medio': 'Medio',
        'grande': 'Grande',
    }

    titulo = models.CharField("Título", max_length=30, unique=True, blank=False, null=False)
    slug = models.SlugField("Slug", unique=True, default='', null=False, blank=True, max_length=255)
    tamanho_botao = models.CharField("Tamanho do Botão",
                                     max_length=10,
                                     choices=tamanhos_botoes,  # type:ignore
                                     default='grande',
                                     blank=False,
                                     null=False)  # type:ignore
    imagem_capa = models.ImageField("Imagem de Capa", upload_to='home/link_capa/', blank=True, default='')
    link_externo = models.BooleanField("Link Externo", blank=False, null=False, default=False)
    url_externo = models.CharField("URL do Link Externo", max_length=2048, blank=True, null=True)
    visivel = models.BooleanField("Visível", blank=False, null=False, default=True)
    conteudo = models.TextField("Conteudo")

    def save(self, *args, **kwargs) -> None:
        if not self.link_externo:
            self.url_externo = ''
        if not self.url_externo and self.link_externo:
            raise ValidationError("Informar URL do Link Externo")

        if not self.slug == slugify(self.titulo):
            self.slug = slugify(self.titulo)

        super_save = super().save(*args, **kwargs)

        # Falta ajustar tamanho imagem

        return super_save

    def __str__(self) -> str:
        return self.titulo
