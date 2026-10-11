"""Barra lateral: modo, historial y archivos."""

from datetime import datetime

import streamlit as st

import config
from services.modes import MODES
from services.session import start_new_chat
from tools.file_processor import process_and_index_file
from tools.history_manager import (
    get_unique_sessions,
    load_session_messages,
    rename_session,
)


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
            # Refresca lista antes de cambiar para no perder el historial en pantalla
            st.session_state.cached_history = get_unique_sessions()
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

        # Siempre recargar desde Supabase para que no desaparezcan
        try:
            st.session_state.cached_history = get_unique_sessions()
        except Exception:
            if "cached_history" not in st.session_state:
                st.session_state.cached_history = []

        # Renombrar conversación actual
        with st.expander("Renombrar conversación actual", expanded=False):
            new_name = st.text_input(
                "Nuevo nombre",
                value=st.session_state.get("chat_title") or "",
                key="rename_input",
                label_visibility="collapsed",
                placeholder="Nombre de la conversación",
            )
            if st.button("Guardar nombre", use_container_width=True):
                if new_name and new_name.strip():
                    ok = rename_session(
                        st.session_state.current_session_id, new_name.strip()
                    )
                    if ok:
                        st.session_state.chat_title = new_name.strip()[:80]
                        st.session_state.cached_history = get_unique_sessions()
                        st.success("Nombre actualizado")
                        st.rerun()
                    else:
                        st.error("No se pudo renombrar. Revisa Supabase.")

        try:
            history = st.session_state.cached_history or []
            if history:
                for chat in history:
                    sid = chat["session_id"]
                    label = chat.get("title") or "Sin título"
                    is_current = sid == st.session_state.current_session_id
                    prefix = "▸ " if is_current else ""
                    if st.button(
                        f"{prefix}{label}",
                        key=f"sid_{sid}",
                        use_container_width=True,
                    ):
                        st.session_state.current_session_id = sid
                        st.session_state.chat_title = label
                        loaded = load_session_messages(sid)
                        if loaded:
                            st.session_state.messages = loaded
                        st.rerun()
            else:
                st.caption(
                    "Aún no hay conversaciones guardadas. "
                    "Escribe un mensaje para crear la primera."
                )
        except Exception:
            st.caption("Historial no disponible. Revisa Supabase.")

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)
        st.caption(f"v0.7 · {datetime.now().strftime('%d/%m/%Y')}")
        st.caption(f"Creado por {config.OWNER_NAME}")
