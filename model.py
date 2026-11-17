from pathlib import Path
from threading import Lock

from ultralytics import YOLO


class SoldaModel:
    def __init__(self, caminho_modelo):
        caminho = Path(caminho_modelo)

        if not caminho.is_file():
            raise FileNotFoundError(
                f"Arquivo do modelo não encontrado: {caminho}"
            )

        self.modelo = YOLO(str(caminho))

        if self.modelo.task != "detect":
            raise ValueError(
                "Esta aplicação espera um modelo de detecção "
                "com caixas retangulares. "
                f"Tarefa encontrada: {self.modelo.task}"
            )

        # Protege o modelo compartilhado durante a inferência.
        self._lock = Lock()

    def detectar(self, imagem_bgr, confianca):
        with self._lock:
            resultados = self.modelo.predict(
                source=imagem_bgr,
                conf=confianca,
                device="cpu",
                verbose=False,
            )

            resultado = resultados[0]

            # Retorna uma imagem BGR com as marcações do YOLO.
            imagem_anotada = resultado.plot()

            deteccoes = []

            if resultado.boxes is not None:
                for caixa in resultado.boxes:
                    x1, y1, x2, y2 = (
                        caixa.xyxy[0].cpu().tolist()
                    )

                    classe_id = int(
                        caixa.cls[0].item()
                    )

                    confianca_detectada = float(
                        caixa.conf[0].item()
                    )

                    deteccoes.append(
                        {
                            "classe": resultado.names[classe_id],
                            "confianca": confianca_detectada,
                            "x1": round(x1, 1),
                            "y1": round(y1, 1),
                            "x2": round(x2, 1),
                            "y2": round(y2, 1),
                        }
                    )

        return imagem_anotada, deteccoes