from pathlib import Path
from django.conf import settings
from PIL import Image

# TODO: Documentar


def redimensionar_imagem(imagem_django, largura_px: int | None = None, altura_px: int | None = None,
                         otimizar=True, qualidade=100, obrigar_largura=True):
    """
    Se somente a largura for enviada a altura será redimensionada proporcionalmente e vice versa.
    Quando largura e altura for None, será redimensionado proporcionalmente para ter no maximo 1200px de largura.
    Obrigar largura False não redimensiona se a largura original for menor que a enviada.
    """
    caminho_imagem = Path(settings.MEDIA_ROOT / imagem_django.name).resolve()
    imagem_pillow = Image.open(caminho_imagem)

    largura_original, altura_original = imagem_pillow.size

    if not obrigar_largura:
        if largura_px:
            largura_px = None if largura_original <= largura_px else largura_px

    if largura_px and not altura_px:
        largura_nova = largura_px
        altura_nova = round(largura_px * altura_original / largura_original)
    elif altura_px and not largura_px:
        largura_nova = round(altura_px * largura_original / altura_original)
        altura_nova = altura_px
    elif largura_px and altura_px:
        largura_nova = largura_px
        altura_nova = altura_px
    else:
        if largura_original <= 1200:
            largura_nova = largura_original
            altura_nova = altura_original
        else:
            largura_nova = 1200
            altura_nova = round(largura_nova * altura_original / largura_original)

    nova_imagem = imagem_pillow.resize((largura_nova, altura_nova), Image.Resampling.LANCZOS)
    nova_imagem.save(caminho_imagem, optimize=otimizar, quality=qualidade)

    return nova_imagem
