from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


class SoldaController:
    LIMITE_BYTES = 20 * 1024 * 1024
    LIMITE_PIXELS = 16_000_000

    def __init__(self, model):
        self.model = model

    def analisar(self, dados_imagem, confianca):
        if not dados_imagem:
            raise ValueError(
                "Selecione uma imagem antes da análise."
            )

        if len(dados_imagem) > self.LIMITE_BYTES:
            raise ValueError(
                "A imagem deve ter no máximo 20 MB."
            )

        if not 0.01 <= confianca <= 1.0:
            raise ValueError(
                "A confiança deve estar entre 0,01 e 1,00."
            )

        try:
            with Image.open(BytesIO(dados_imagem)) as original:
                if original.format not in {"JPEG", "PNG"}:
                    raise ValueError(
                        "Utilize uma imagem JPEG ou PNG."
                    )

                largura, altura = original.size

                if largura * altura > self.LIMITE_PIXELS:
                    raise ValueError(
                        "A imagem deve ter no máximo "
                        "16 milhões de pixels."
                    )

                # Corrige a orientação registrada pela câmera.
                imagem_rgb = ImageOps.exif_transpose(
                    original
                ).convert("RGB")

                imagem_array = np.array(imagem_rgb)

        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
        ) as erro:
            raise ValueError(
                "O arquivo não pôde ser lido como imagem válida."
            ) from erro

        # O YOLO aceita imagens NumPy em formato BGR.
        imagem_bgr = cv2.cvtColor(
            imagem_array,
            cv2.COLOR_RGB2BGR,
        )

        imagem_anotada, deteccoes = self.model.detectar(
            imagem_bgr,
            confianca,
        )

        sucesso, imagem_codificada = cv2.imencode(
            ".png",
            imagem_anotada,
        )

        if not sucesso:
            raise RuntimeError(
                "Não foi possível preparar a imagem de saída."
            )

        return {
            "imagem_png": imagem_codificada.tobytes(),
            "deteccoes": deteccoes,
            "largura": imagem_array.shape[1],
            "altura": imagem_array.shape[0],
        }