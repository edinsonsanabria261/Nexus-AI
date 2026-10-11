"""Barra lateral: modo, historial y archivos."""

from datetime import datetime

import streamlit as st

import config
from services.modes import MODES
from services.session import start_new_chat
from tools.file_processor import process_and_index_file
from tools.history_manager import get_unique_sessions, load_session_messages


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("**Modo IA**")
        labels = [mode["label"] for mode in MODES]
        ids = [mode["id"] for mode in MODES]
        current = st.session_state.ia_mode
        index = ids.index(current) if current in ids else 0
        chosen = st.radio(
            "Modo IA",
            labels,
            index=index,
            label_visibility="collapsed",
        )
        st.session_state.ia_mode = ids[labels.index(chosen)]
        blurb = next(mode["blurb"] for mode in MODES if mode["label"] == chosen)
        st.caption(blurb)

        st.divider()
        if st.button("Nueva conversación", use_container_width=True):
            start_new_chat()
            st.rerun()

        st.divider()
        st.session_state.use_web_search = st.toggle(
            "Resultados rápidos de la Web",
            value=st.session_state.use_web_search,
        )
        st.caption("En Todo, la web es opcional. En los otros modos siempre se consulta.")

        st.divider()
        st.markdown("**Documentos**")
        uploaded = st.file_uploader(
            "Cargar archivo",
            type=["pdf", "txt", "py", "js", "json", "md", "docx", "doc", "xlsx"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            file_key = f"proc_{uploaded.name}_{uploaded.size}"
            if file_key not in st.session_state:
                with st.spinner("Indexando..."):
                    saved = process_and_index_file(uploaded.read(), uploaded.name)
                st.session_state[file_key] = True
                if saved > 0:
                    st.success(f"{uploaded.name}: {saved} bloques guardados.")
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": (
                                f"El archivo `{uploaded.name}` quedó indexado "
                                f"({saved} bloques)."
                            ),
                        }
                    )
                else:
                    st.error("No se pudo extraer texto o guardarlo en la memoria.")

        st.divider()
        st.markdown("**Conversaciones**")
        try:
            if not st.session_state.cached_history:
                st.session_state.cached_history = get_unique_sessions()
            if st.session_state.cached_history:
                for chat in st.session_state.cached_history:
                    label = chat.get("title") or "Sin título"
                    if st.button(
                        label,
                        key=f"sid_{chat['session_id']}",
                        use_container_width=True,
                    ):
                        st.session_state.current_session_id = chat["session_id"]
                        st.session_state.chat_title = label
                        loaded = load_session_messages(chat["session_id"])
                        if loaded:
                            st.session_state.messages = loaded
                        st.rerun()
            else:
                st.caption("Todavía no hay conversaciones guardadas.")
        except Exception:
            st.caption("Historial no disponible. Revisa Supabase.")

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)
        st.caption(f"v0.7 · {datetime.now().strftime('%Y-%m-%d')}")
        st.caption(f"Creado por {config.OWNER_NAME}")
