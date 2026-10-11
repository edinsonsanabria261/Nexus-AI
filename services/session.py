"""Estado de la conversación en Streamlit."""

import uuid
import streamlit as st
import config


def welcome_message() -> dict:
    return {
        "role": "assistant",
        "content": (
            f"Hola, soy **{config.BOT_NAME}**.\n\n"
            "Puedo ayudarte con preguntas generales y con ciberseguridad defensiva. "
            "Arriba, en Modo IA, elige Todo, Imágenes, Videos, Noticias, Libros o Finanzas.\n\n"
            "Para guardar una nota: `recuerda esto: [texto]`.\n\n"
            "Consultas rápidas: `cve`, `whois`, `dns`, `ip`, `headers` y `hash`."
        ),
    }


def init_session_state() -> None:
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = str(uuid.uuid4())
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = "Nueva conversación"
    if "messages" not in st.session_state:
        st.session_state.messages = [welcome_message()]
    if "use_web_search" not in st.session_state:
        st.session_state.use_web_search = True
    if "ia_mode" not in st.session_state:
        st.session_state.ia_mode = "todo"
    if "cached_history" not in st.session_state:
        st.session_state.cached_history = []


def start_new_chat() -> None:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.chat_title = "Nueva conversación"
    st.session_state.messages = [welcome_message()]
