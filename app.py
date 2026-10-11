"""Punto de entrada de NexusSec AI. La interfaz vive en ui/ y la lógica en services/."""

import streamlit as st

import config
from services.chat import generate_response
from services.modes import mode_label
from services.session import init_session_state
from tools.history_manager import get_unique_sessions, save_chat_message
from ui.chat_view import render_messages
from ui.sidebar import render_sidebar
from ui.theme import inject_theme


def main() -> None:
    st.set_page_config(
        page_title=config.BOT_NAME,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    init_session_state()
    render_sidebar()

    mode_name = mode_label(st.session_state.ia_mode)
    st.markdown(
        f"""
        <div class="main-header">
            <h1>{config.BOT_NAME}</h1>
            <p>Modo IA · {mode_name} · Ciberseguridad avanzada</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_messages(st.session_state.messages)

    prompt = st.chat_input(f"Pregunta a {config.BOT_NAME}...")
    if not prompt:
        return

    # Título = primera pregunta del usuario
    if len(st.session_state.messages) <= 1:
        st.session_state.chat_title = prompt[:60]

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    try:
        save_chat_message(
            st.session_state.current_session_id,
            st.session_state.chat_title,
            "user",
            prompt,
        )
        st.session_state.cached_history = get_unique_sessions()
    except Exception:
        pass

    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Consultando..."):
            response = generate_response(
                prompt,
                st.session_state.messages[:-1],
                st.session_state.use_web_search,
                st.session_state.ia_mode,
            )
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    try:
        save_chat_message(
            st.session_state.current_session_id,
            st.session_state.chat_title,
            "assistant",
            response,
        )
        st.session_state.cached_history = get_unique_sessions()
    except Exception:
        pass


if __name__ == "__main__":
    main()
