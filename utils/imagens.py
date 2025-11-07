from pathlib import Path
from django.conf import settings
from PIL import Image


def redimensionar_imagem(imagem_django, largura_px: int | None = None, altura_px: int | None = None,
                         otimizar=True, qualidade=100, obrigar_largura=True):
    """Redimensiona o tamanho de imagens Django.

    Parametros:
    -----------
    :imagem_django [FieldFile | ImageFieldFile]: com o campo de imagem a ser redimensionada.
    :largura_px [int | None, Default None]: com a nova largura em pixel. Se for None a nova largura será proporcional ao enviado em altura_px, se altura também for None, a largura será no maximo 1200px.
    :altura_px [int | None, Default None]: com a nova altura em pixel. Se for None a nova altura será proporcional ao enviado em largura_px.
    :otimizar [bool, Default True]: booleano se o tamanho de armazenamento será otimizado.
    :qualidade [int, Default 100]: com o percentual de qualidade da nova imagem.
    :obrigar_largura [bool, Default True]: booleano quando False não redimensiona se a largura original for menor que a enviada.

    Retorno:
    --------
    :Image: com a imagem redimensionada."""
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
