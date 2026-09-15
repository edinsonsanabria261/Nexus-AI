import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge

# Configuración de página limpia
st.set_page_config(
    page_title=config.BOT_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección estricta de CSS para evitar parpadeos y mantener el modo oscuro
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
        background-color: #1c1c1c; padding: 1.2rem 1.6rem;
        border-radius: 16px; border: 1px solid #3a3a3a;
        margin-bottom: 1.5rem; display: flex; align-items: center; gap: 14px;
    }
    .main-header h1 { margin: 0; font-size: 1.5rem; font-weight: 600; color: #ffffff !important; }
    .main-header p { margin: 0; font-size: 0.9rem; color: #b0b3b8 !important; }
    .stButton > button {
        background-color: #2a2a2a !important; color: #ffffff !important;
        border: 1px solid #555555 !important; border-radius: 12px !important;
    }
    .stChatInput textarea { background-color: #1f1f1f !important; color: #ffffff !important; border-radius: 24px !important; }
    code { background-color: #2a2a2a !important; color: #8ab4f8 !important; }
    </style>
    """,
    unsafe_allow_html=True
)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nAsistente de ciberseguridad con memoria persistente.\n\nPuedes enseñarme con:\n`recuerda esto: [texto]`\n\n¿En qué puedo ayudarte?"
        }]
    if "use_web_search" not in st.session_state:
        st.session_state.use_web_search = True

def get_client():
    if not config.GROQ_API_KEY:
        return None
    return Groq(api_key=config.GROQ_API_KEY)

def generate_response(question):
    client = get_client()
    if not client:
        return "❌ Error: Falta configurar la variable 'GROQ_API_KEY' en tu entorno de Render."

    q_lower = question.lower().strip()
    
    # Procesar comando manual de aprendizaje externo
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"🧠 **Guardado en memoria persistente con éxito:**\n\n> {knowledge}"
            return "❌ Error al intentar conectar o guardar en la base de datos. Verifica la conexión externa."
        return "⚠️ Por favor, escribe información válida después del comando `recuerda esto:`"

    # 1. Búsqueda en Base de Datos de Memoria (RAG)
    memory_hits = search_knowledge(question, limit=4)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join([f"- {m['content']}" for m in memory_hits])

    # 2. Búsqueda de información en la Web
    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("🔍 Rastreando fuentes web actualizadas..."):
            try:
                web_text = search_and_read(question, max_results=3, read_full=True)
            except Exception:
                web_text = ""

    # 3. Construcción del Prompt del Sistema Dinámico
    # Al inyectar el contexto aquí, la IA sabe de dónde viene la información y responde con propiedad.
    custom_system_prompt = config.SYSTEM_PROMPT
    if memory_text or web_text:
        custom_system_prompt += "\n\n[CONTEXTO ADICIONAL RECUPERADO DE TUS SISTEMAS]"
        if memory_text:
            custom_system_prompt += f"\n- Conocimientos previos guardados en tu base de datos:\n{memory_text}"
        if web_text:
            custom_system_prompt += f"\n- Información en tiempo real recopilada de la Web:\n{web_text}"
        custom_system_prompt += "\nUtiliza este contexto únicamente si es directamente relevante para responder la solicitud del usuario de forma técnica y precisa."

    # Configurar el mensaje base del sistema modificado
    messages = [{"role": "system", "content": custom_system_prompt}]
    
    # Mantener el historial de la conversación (Últimos 6 mensajes para control de tokens)
    for msg in st.session_state.messages[-6:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    # Mensaje final del usuario limpio sin contaminación de metadatos
    messages.append({"role": "user", "content": question})

    try:
        res = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.25,  # Bajado a 0.25 para asegurar mayor precisión técnica en ciberseguridad
            max_tokens=2500
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Error en la API de Groq: {e}"

def main():
    init_session_state()

    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.9rem;">🛡️</div>
        <div>
            <h1>{config.BOT_NAME}</h1>
            <p>Asistente de Ciberseguridad Experto · Entorno de Operaciones</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### ⚡ Panel de Control")
        st.caption("NexusSec Artificial Intelligence")
        st.divider()

        if st.button("🔄 Nueva conversación", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Nueva conversación iniciada. Dispuesto para análisis de infraestructura, reportes o auditoría de código."
            }]
            st.rerun()

        st.divider()
        st.session_state.use_web_search = st.toggle("🌐 Módulo OSINT / Web Search", value=st.session_state.use_web_search)

        st.divider()
        st.markdown("**Core LLM Engine:**")
        st.code(config.GROQ_MODEL, language=None)

        st.divider()
        st.markdown("**Comando Base de Aprendizaje:**")
        st.code("recuerda esto: <información>", language=None)

        st.divider()
        st.caption(f"Versión Actual: v0.3")
        st.caption(f"Desarrollado de forma élite por {config.OWNER_NAME}")

    # Renderizar el feed histórico del chat
    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Entrada de comandos de usuario
    if prompt := st.chat_input(f"Escribe un comando o consulta para {config.BOT_NAME}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🛡️"):
            response = generate_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
