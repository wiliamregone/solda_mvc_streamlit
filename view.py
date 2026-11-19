import hashlib
import logging

import streamlit as st


logger = logging.getLogger(__name__)


def mostrar_interface(controller):
    st.title("Inspeção visual de soldagem")

    st.caption(
        "Detecção com YOLO, arquitetura MVC e Streamlit"
    )

    st.write(
        "Selecione uma imagem ou capture uma fotografia "
        "para realizar a análise."
    )

    # 1. Escolher a origem da imagem.
    origem = st.radio(
        "Como deseja fornecer a imagem?",
        options=[
            "Selecionar arquivo",
            "Usar câmera",
        ],
        key="origem_imagem",
    )

    # 2. Disponibilizar o componente correspondente.
    if origem == "Selecionar arquivo":
        arquivo = st.file_uploader(
            "Selecione uma imagem JPG, JPEG ou PNG",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            key="upload_imagem_solda",
            help=(
                "Aceita JPG, JPEG e PNG, incluindo "
                "extensões escritas em letras maiúsculas."
            ),
        )

    else:
        st.info(
            "Autorize o acesso à câmera quando "
            "o navegador solicitar."
        )

        arquivo = st.camera_input(
            "Capture uma imagem da solda",
            key="camera_imagem_solda",
        )

        st.caption(
            "Se a câmera não abrir, confira as permissões "
            "do navegador ou utilize Selecionar arquivo."
        )

    # 3. Configurar a análise.
    confianca = st.slider(
        "Confiança mínima",
        min_value=0.05,
        max_value=0.95,
        value=0.20,
        step=0.05,
        help=(
            "Valores menores podem apresentar mais detecções, "
            "incluindo possíveis falsos positivos."
        ),
    )

    limite_mb = controller.LIMITE_BYTES / (1024 * 1024)
    limite_mp = controller.LIMITE_PIXELS / 1_000_000

    st.caption(
        f"Limites: {limite_mb:.0f} MB por arquivo "
        f"e {limite_mp:g} milhões de pixels."
    )

    # 4. Aguardar uma imagem.
    if arquivo is None:
        st.session_state.pop("analise_solda", None)

        st.info(
            "Selecione um arquivo ou capture uma fotografia."
        )

        return

    # Upload e câmera disponibilizam bytes em memória.
    dados = arquivo.getvalue()

    if not dados:
        st.session_state.pop("analise_solda", None)
        st.error("A imagem recebida está vazia.")
        return

    if len(dados) > controller.LIMITE_BYTES:
        st.session_state.pop("analise_solda", None)

        st.error(
            f"O arquivo ultrapassa o limite de {limite_mb:.0f} MB."
        )

        return

    # 5. Identificar a imagem e a configuração utilizadas.
    assinatura = (
        origem,
        hashlib.sha256(dados).hexdigest(),
        confianca,
    )

    analise_salva = st.session_state.get("analise_solda")

    if (
        analise_salva is not None
        and analise_salva["assinatura"] != assinatura
    ):
        st.session_state.pop("analise_solda", None)

    st.write(f"Imagem recebida: {arquivo.name}")

    st.caption(
        f"Tamanho recebido: {len(dados) / (1024 * 1024):.2f} MB"
    )

    # 6. Solicitar a análise ao Controller.
    if st.button(
        "Analisar imagem",
        type="primary",
        key="botao_analisar_solda",
    ):
        st.session_state.pop("analise_solda", None)

        try:
            with st.spinner("Processando a imagem..."):
                resultado = controller.analisar(
                    dados,
                    confianca,
                )

        except ValueError as erro:
            st.error(str(erro))

        except Exception:
            logger.exception("Falha na análise da imagem.")

            st.error(
                "Não foi possível concluir a análise. "
                "Consulte os registros de execução."
            )

        else:
            st.session_state["analise_solda"] = {
                "assinatura": assinatura,
                "resultado": resultado,
            }

    # 7. Recuperar e apresentar o resultado.
    analise_salva = st.session_state.get("analise_solda")

    if analise_salva is None:
        return

    resultado = analise_salva["resultado"]
    deteccoes = resultado["deteccoes"]

    st.subheader("Resultado da análise")

    st.image(
        resultado["imagem_png"],
        caption="Imagem com as marcações do modelo",
    )

    coluna1, coluna2 = st.columns(2)

    coluna1.metric(
        "Regiões detectadas",
        len(deteccoes),
    )

    coluna2.metric(
        "Dimensões analisadas",
        f'{resultado["largura"]} × {resultado["altura"]}',
    )

    if deteccoes:
        tabela = []

        for deteccao in deteccoes:
            linha = deteccao.copy()

            linha["confianca"] = (
                f'{deteccao["confianca"]:.1%}'
            )

            tabela.append(linha)

        st.dataframe(
            tabela,
            hide_index=True,
        )

    else:
        st.info(
            "Nenhuma detecção acima da confiança selecionada. "
            "Isso não comprova a ausência de defeitos."
        )

    # 8. Disponibilizar o download.
    st.download_button(
        label="Baixar imagem anotada",
        data=resultado["imagem_png"],
        file_name="solda_analisada.png",
        mime="image/png",
        key="download_imagem_solda",
    )

    st.caption(
        "As coordenadas estão em pixels. "
        "A confiança não representa uma medida "
        "direta da qualidade da solda."
    )