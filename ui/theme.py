"""Estilos de la interfaz."""

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background-color: #0d0d0d; color: #f1f3f4; }
        section[data-testid="stSidebar"] {
            background-color: #161616 !important;
            border-right: 1px solid #333333 !important;
        }
        section[data-testid="stSidebar"] * { color: #f1f3f4 !important; }
        .main-header {
            background-color: #1c1c1c;
            padding: 1.2rem 1.6rem;
            border-radius: 16px;
            border: 1px solid #3a3a3a;
            margin-bottom: 1.1rem;
        }
        .main-header h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
            color: #ffffff !important;
        }
        .main-header p { margin: 0.2rem 0 0; font-size: 0.9rem; color: #b0b3b8 !important; }
        .stButton > button {
            background-color: #2a2a2a !important;
            color: #ffffff !important;
            border: 1px solid #555555 !important;
            border-radius: 12px !important;
        }
        .stChatInput textarea {
            background-color: #1f1f1f !important;
            color: #ffffff !important;
            border-radius: 24px !important;
        }
        code { background-color: #2a2a2a !important; color: #8ab4f8 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
