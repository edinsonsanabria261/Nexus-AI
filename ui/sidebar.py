"""Barra lateral estilo lista de conversaciones (tipo Grok)."""

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
from tools.memory import get_supabase


def render_sidebar() -> None:
    with st.sidebar:
        # --- Nueva conversación (arriba, como Grok) ---
        if st.button("✎  Nueva conversación", use_container_width=True, type="primary"):
            st.session_state.cached_history = get_unique_sessions()
            start_new_chat()
            st.rerun()

        st.divider()

        # --- Modo IA ---
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

        st.divider()
        st.session_state.use_web_search = st.toggle(
            "Buscar en la web",
            value=st.session_state.use_web_search,
        )

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
                    st.success(f"{uploaded.name}: {saved} bloques.")
                else:
                    st.error("No se pudo indexar el archivo.")

        st.divider()

        # --- Conversaciones (estilo lista Grok) ---
        st.markdown("**Conversaciones**")

        sb = get_supabase()
        if not sb:
            st.warning(
                "Historial desconectado. Revisa SUPABASE_URL y SUPABASE_KEY en Render."
            )
            history = []
        else:
            try:
                history = get_unique_sessions(limit=50)
                st.session_state.cached_history = history
            except Exception as exc:
                st.warning(f"No se pudo cargar el historial: {exc}")
                history = st.session_state.get("cached_history") or []

        # Renombrar actual
        with st.expander("Renombrar actual", expanded=False):
            new_name = st.text_input(
                "Nombre",
                value=st.session_state.get("chat_title") or "",
                key="rename_input",
                label_visibility="collapsed",
                placeholder="Nuevo nombre",
            )
            if st.button("Guardar nombre", use_container_width=True, key="btn_rename"):
                if new_name and new_name.strip():
                    if rename_session(
                        st.session_state.current_session_id, new_name.strip()
                    ):
                        st.session_state.chat_title = new_name.strip()[:80]
                        st.session_state.cached_history = get_unique_sessions()
                        st.rerun()
                    else:
                        st.error("No se pudo renombrar.")

        if history:
            show_all = st.session_state.get("show_all_chats", False)
            visible = history if show_all else history[:8]

            for chat in visible:
                sid = chat["session_id"]
                label = (chat.get("title") or "Sin título")[:48]
                is_current = sid == st.session_state.current_session_id
                btn_label = f"▸ {label}" if is_current else label

                if st.button(
                    btn_label,
                    key=f"sid_{sid}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary",
                ):
                    st.session_state.current_session_id = sid
                    st.session_state.chat_title = label
                    loaded = load_session_messages(sid)
                    if loaded:
                        st.session_state.messages = loaded
                    st.rerun()

            if len(history) > 8:
                if st.button(
                    "Ver todas" if not show_all else "Ver menos",
                    use_container_width=True,
                    key="toggle_all_chats",
                ):
                    st.session_state.show_all_chats = not show_all
                    st.rerun()
        else:
            if sb:
                st.caption(
                    "Aún no hay conversaciones. Escribe un mensaje y se guardará aquí."
                )

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)
        st.caption(f"v0.8 · {datetime.now().strftime('%d/%m/%Y')}")
        st.caption(f"Creado por {config.OWNER_NAME}")
