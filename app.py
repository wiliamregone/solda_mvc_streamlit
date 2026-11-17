import logging
from pathlib import Path

import streamlit as st

from controller import SoldaController
from model import SoldaModel
from view import mostrar_interface


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Inspeção de soldagem",
    page_icon="🔎",
    layout="centered",
)


@st.cache_resource
def carregar_modelo(caminho):
    return SoldaModel(caminho)


pasta_projeto = Path(__file__).resolve().parent

caminho_modelo = (
    pasta_projeto
    / "pesos"
    / "best_YOLO_26.pt"
)

try:
    model = carregar_modelo(str(caminho_modelo))

except Exception:
    logger.exception("Falha ao carregar o modelo.")

    st.error(
        "Não foi possível carregar o modelo. "
        "Confira o arquivo de pesos e as dependências."
    )

    st.stop()

controller = SoldaController(model)

mostrar_interface(controller)