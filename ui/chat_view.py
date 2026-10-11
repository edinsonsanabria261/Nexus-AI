"""Render del historial visible."""

import streamlit as st


def render_messages(messages: list) -> None:
    for msg in messages:
        avatar = "N" if msg["role"] == "assistant" else "U"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
