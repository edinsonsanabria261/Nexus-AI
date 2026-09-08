"""
NexusSec AI - Chatbot de Ciberseguridad
Proyecto de Edinson - 2026
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

# === Estilos personalizados ===
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    .main-header {
        background: linear-gradient(90deg, #dc2626 0%, #991b1b 50%, #7f1d1d 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(220, 38, 38, 0.3);
    }
    .source-box {
        background: #1e293b;
        border-left: 4px solid #dc2626;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    div[data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.6);
        border-radius: 12px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\n"
                           f"Asistente de ciberseguridad de {config.OWNER_NAME}.\n\n"
                           "Puedo ayudarte con vulnerabilidades, pentesting ético, forense, "
                           "hardening, OWASP, análisis de amenazas y mucho más.\n\n"
                           "También puedo **buscar información actualizada en la web** cuando lo necesites.\n\n"
                           "¿En qué puedo ayudarte hoy?"
            }
        ]
    if "use_web_search" not in st.session_state:
        st.session_state.use_web_search = True


def get_groq_client():
    if not config.GROQ_API_KEY:
        return None
    return Groq(api_key=config.GROQ_API_KEY)


def build_messages_for_llm(user_question: str, web_context: str = "") -> list:
    """Construye el historial + contexto web para enviar al modelo."""
    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]

    # Agregamos un poco de historial (últimos 6 mensajes para no saturar contexto)
    history = st.session_state.messages[-6:]
    for msg in history:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Si hay contexto de web, lo inyectamos
    if web_context:
        enhanced = (
            f"El usuario preguntó: {user_question}\n\n"
            f"### Información actualizada de la web (úsal a para responder):\n"
            f"{web_context}\n\n"
            f"Responde de forma precisa citando las fuentes cuando uses esta información."
        )
        messages.append({"role": "user", "content": enhanced})
    else:
        messages.append({"role": "user", "content": user_question})

    return messages


def generate_response(user_question: str) -> str:
    client = get_groq_client()
    if client is None:
        return ("⚠️ **Falta la API Key de Groq**.\n\n"
                "1. Ve a https://console.groq.com/keys\n"
                "2. Crea una API Key gratuita\n"
                "3. Crea un archivo `.env` en la raíz del proyecto con:\n"
                "```\nGROQ_API_KEY=gsk_tu_clave_aqui\n```\n"
                "4. Reinicia la aplicación.")

    web_context = ""
    if st.session_state.use_web_search:
        with st.spinner("🔍 Buscando información actualizada en la web..."):
            # Mejoramos la query para ciberseguridad
            search_query = f"cybersecurity {user_question}" if len(user_question) < 60 else user_question
            web_context = search_and_read(search_query, max_results=3, read_full=True)

    messages = build_messages_for_llm(user_question, web_context)

    try:
        completion = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            top_p=0.9,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error al contactar el modelo: {str(e)}"


def main():
    init_session_state()

    # === Header ===
    st.markdown(f"""
    <div class="main-header">
        <h1 style="margin:0; font-size:1.8rem;">🛡️ {config.BOT_NAME}</h1>
        <p style="margin:0.3rem 0 0 0; opacity:0.9;">Asistente de Ciberseguridad · Proyecto de {config.OWNER_NAME}</p>
    </div>
    """, unsafe_allow_html=True)

    # === Sidebar ===
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
        st.title("Configuración")

        st.session_state.use_web_search = st.toggle(
            "🔍 Buscar en la web",
            value=st.session_state.use_web_search,
            help="Cuando está activado, el bot busca información actualizada antes de responder."
        )

        st.divider()
        st.markdown("**Modelo actual:**")
        st.code(config.GROQ_MODEL, language=None)

        st.divider()
        st.markdown("### Acciones")
        if st.button("🗑️ Limpiar conversación", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": f"Conversación reiniciada. ¿En qué puedo ayudarte, {config.OWNER_NAME}?"
                }
            ]
            st.rerun()

        st.divider()
        st.markdown("""
        **Próximas mejoras del proyecto:**
        - 📚 RAG con tus PDFs y reportes
        - 🛠️ Herramientas (whois, CVE lookup...)
        - 🧠 Memoria a largo plazo
        - 🔗 Integración con Nexus-Sec
        """)

        st.caption(f"v0.1.0 · {datetime.now().strftime('%Y-%m-%d')}")

    # === Chat ===
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu pregunta de ciberseguridad..."):
        # Mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generar respuesta
        with st.chat_message("assistant"):
            response = generate_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
