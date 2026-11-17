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
        "Envie uma imagem JPEG ou PNG para identificar "
        "as classes aprendidas pelo modelo."
    )

    arquivo = st.file_uploader(
        "Selecione uma imagem",
        type=["jpg", "jpeg", "png"],
    )

    confianca = st.slider(
        "Confiança mínima",
        min_value=0.05,
        max_value=0.95,
        value=0.20,
        step=0.05,
        help=(
            "Valores menores podem mostrar mais detecções, "
            "incluindo possíveis falsos positivos."
        ),
    )

    st.caption(
        "Limites desta aplicação: 20 MB por arquivo "
        "e 16 milhões de pixels por imagem."
    )

    if arquivo is None:
        st.session_state.pop("analise_solda", None)
        st.info("Selecione uma imagem para começar.")
        return

    dados = arquivo.getvalue()

    if len(dados) > controller.LIMITE_BYTES:
        st.session_state.pop("analise_solda", None)
        st.error("O arquivo ultrapassa o limite de 20 MB.")
        return

    # Identifica a combinação imagem + configuração.
    assinatura = (
        hashlib.sha256(dados).hexdigest(),
        confianca,
    )

    analise_salva = st.session_state.get("analise_solda")

    # Descarta resultados de outra imagem ou configuração.
    if (
        analise_salva is not None
        and analise_salva["assinatura"] != assinatura
    ):
        st.session_state.pop("analise_solda", None)

    st.write(f"Arquivo selecionado: {arquivo.name}")

    if st.button("Analisar imagem", type="primary"):
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

    st.download_button(
        label="Baixar imagem anotada",
        data=resultado["imagem_png"],
        file_name="solda_analisada.png",
        mime="image/png",
    )

    st.caption(
        "As coordenadas estão em pixels. "
        "A confiança não representa uma medida "
        "direta da qualidade da solda."
    )