"""
NexusSec AI - Chatbot de Ciberseguridad
Interfaz mejorada estilo Gemini
"""

import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read

# === Configuración de página ===
st.set_page_config(
    page_title=f"{config.BOT_NAME} | Ciberseguridad",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS personalizado (estilo Gemini oscuro) ===
st.markdown("""
<style>
    /* Fondo general */
    .stApp {
        background-color: #0f0f0f;
        color: #e8eaed;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #2d2d2d;
    }

    /* Header limpio */
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

    /* Burbujas de chat */
