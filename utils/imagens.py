from pathlib import Path
from django.conf import settings
from PIL import Image


def redimensionar_imagem(imagem_django, largura_px: int | None = None, altura_px: int | None = None,
                         otimizar=True, qualidade=100):
    """Se somente a largura for enviada a altura será redimensionada proporcionalmente e vice versa"""
    caminho_imagem = Path(settings.MEDIA_ROOT / imagem_django.name).resolve()
    imagem_pillow = Image.open(caminho_imagem)

    largura_original, altura_original = imagem_pillow.size

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
        imagem_pillow.close()
        return imagem_pillow

    nova_imagem = imagem_pillow.resize((largura_nova, altura_nova), Image.Resampling.LANCZOS)
    nova_imagem.save(caminho_imagem, optimize=otimizar, quality=qualidade)

    return nova_imagem
