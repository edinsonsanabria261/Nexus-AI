"""
NexusSec AI - Chatbot de Ciberseguridad
Con memoria persistente (Supabase)
"""

import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge, get_recent_knowledge

# === Configuración de página ===
st.set_page_config(
    page_title=f"{config.BOT_NAME} | Ciberseguridad",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS estilo Gemini oscuro ===
st.markdown("""
<style>
    .stApp {
        background-color: #0f0f0f;
        color: #e8eaed;
    }
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #2d2d2d;
    }
    .main-header {
        background: linear-gradient(90deg, #1a1a1a 0%, #252525 100%);
        padding: 1.1rem 1.5rem;
        border-radius: 16px;
        border: 1px solid #333;
        margin-bottom: 1.8rem;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.45rem;
        font-weight: 600;
        color: #f1f3f4;
    }
    .main-header p {
        margin: 0;
        font-size: 0.85rem;
        color: #9aa0a6;
    }
    .stButton > button {
        border-radius: 12px;
        border: 1px solid #3c4043;
        background-color: #2d2d2d;
        color: #e8eaed;
    }
    code {
        background-color: #2d2d2d !important;
        color: #8ab4f8 !important;
        padding: 0.2rem 0.45rem;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\n"
                           f"Asistente de ciberseguridad de {config.OWNER_NAME} con **memoria persistente**.\n\n"
                           "Puedes enseñarme cosas con el comando:\n"
