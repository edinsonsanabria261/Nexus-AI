import streamlit as st
import uuid
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge
from tools.file_processor import process_and_index_file

# Importación segura del gestor de historial
try:
    from tools.history_manager import save_chat_message, get_unique_sessions, load_session_messages
    HAS_HISTORY = True
except Exception:
    HAS_HISTORY = False

st.set_page_config(
    page_title=config.BOT_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS seguro para mantener tu paleta de colores original y el modo oscuro empresarial
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d0d0d;
        color: #f1f3f4;
    }
    section[data-testid="stSidebar"] {
        background-color: #161616 !important;
        border-right: 1px solid #333333 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #f1f3f4 !important;
    }
    .main-header {
        background-color: #1c1c1c;
        padding: 1.2rem 1.6rem;
        border-radius: 16px;
        border: 1px solid #3a3a3a;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff !important;
    }
    .main-header p {
        margin: 0;
        font-size: 0.9rem;
        color: #b0b3b8 !important;
    }
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
    code {
        background-color: #2a2a2a !important;
        color: #8ab4f8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def init_session_state():
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = str(uuid.uuid4())
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = "Nueva conversación"
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nInteligencia Artificial para ciberseguridad con memoria persistente.\n\nPuedes enseñarme con:\n`recuerda esto: [texto]`\n\n¿En qué puedo ayudarte?"
        }]
    if "use_web_search" not in st.session_state:
        st.session_state.use_web_search = True
    if "cached_history" not in st.session_state:
        st.session_state.cached_history = []


def get_client():
    if not config.GROQ_API_KEY:
        return None
    return Groq(api_key=config.GROQ_API_KEY)


def generate_response(question):
    client = get_client()
    if not client:
        return "Falta GROQ_API_KEY en Render."

    q_lower = question.lower().strip()
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1).strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"Guardado en memoria persistente:\n\n> {knowledge}"
            return "Error al guardar en Supabase. Revisa la conexion."
        return "Escribe algo despues de 'recuerda esto:'"

    memory_hits = search_knowledge(question, limit=4)
    memory_text = "\n".join([f"- {m['content']}" for m in memory_hits]) if memory_hits else ""

    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("Buscando informacion..."):
            try:
                web_text = search_and_read(question, max_results=3, read_full=True)
            except Exception:
                web_text = ""

    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    for msg in st.session_state.messages[-6:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    extra = ""
    if memory_text:
        extra += f"\n\nConocimiento guardado:\n{memory_text}"
    if web_text:
        extra += f"\n\nInformacion de la web:\n{web_text}"

    final_q = question if not extra else f"{question}\n{extra}"
    messages.append({"role": "user", "content": final_q})

    try:
        res = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.25,
            max_tokens=2500
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error en API de Groq: {e}"


def main():
    init_session_state()

    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.9rem;">🛡️</div>
        <div>
            <h1>{config.BOT_NAME}</h1>
            <p>Inteligencia Artificial de Ciberseguridad</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### {config.BOT_NAME}")
        st.caption("Ciberseguridad avanzada")
        st.divider()

        if st.button("Nueva conversacion", use_container_width=True):
            if HAS_HISTORY:
                try:
                    st.session_state.cached_history = get_unique_sessions()
                except Exception:
                    pass
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.chat_title = "Nueva conversación"
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Nueva conversacion iniciada. ¿En que puedo ayudarte?"
            }]
            st.rerun()

        st.divider()
        st.session_state.use_web_search = st.toggle("Buscar en la web", value=st.session_state.use_web_search)

        st.divider()
        st.markdown("**Analizador Multimodal**")
        uploaded_file = st.file_uploader(
            "Cargar archivo:", 
            type=["pdf", "txt", "py", "js", "json", "md", "docx", "doc", "xlsx"],
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            f_key = f"proc_{uploaded_file.name}_{uploaded_file.size}"
            if f_key not in st.session_state:
                with st.spinner("Indexando..."):
                    saved = process_and_index_file(uploaded_file.read(), uploaded_file.name)
                    if saved > 0:
                        st.success(f"¡{uploaded_file.name} procesado! {saved} bloques guardados.")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"⚙️ **Sistema:** El archivo `{uploaded_file.name}` ha sido indexado con éxito ({saved} bloques). Ya puedes consultarme sobre su contenido."
                        })
                    else:
                        st.error("No se pudo extraer texto legible del archivo.")
                st.session_state[f_key] = True

        st.divider()
        st.markdown("**Conversaciones Recientes**")
        if HAS_HISTORY:
            try:
                # Si no hay caché, traemos las sesiones de Supabase de forma limpia
                if not st.session_state.cached_history:
                    st.session_state.cached_history = get_unique_sessions()
                
                if st.session_state.cached_history:
                    for chat in st.session_state.cached_history:
                        b_key = f"sid_{chat['session_id']}"
                        if st.button(f"💬 {chat['title']}", key=b_key, use_container_width=True):
                            st.session_state.current_session_id = chat['session_id']
                            st.session_state.chat_title = chat['title']
                            db_messages = load_session_messages(chat['session_id'])
                            if db_messages:
                                st.session_state.messages = db_messages
                            st.rerun()
                else:
                    st.caption("No hay hilos grabados.")
            except Exception:
                st.caption("Historial temporalmente en pausa.")
        else:
            st.caption("Módulo de historial desactivado.")

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)

        st.divider()
        st.markdown("**Aprender**")
        st.code("recuerda esto: tu texto", language=None)

        st.divider()
        st.caption(f"v0.6 · {datetime.now().strftime('%Y-%m-%d')}")
        st.caption(f"Creado por {config.OWNER_NAME}")

    # Renderizar el feed histórico del chat
    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input(f"Pregunta a {config.BOT_NAME}..."):
        if len(st.session_state.messages) <= 1:
            st.session_state.chat_title = prompt[:30]

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        if HAS_HISTORY:
            try:
                save_chat_message(st.session_state.current_session_id, st.session_state.chat_title, "user", prompt)
            except Exception:
                pass

        with st.chat_message("assistant", avatar="🛡️"):
            response = generate_response(prompt)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        if HAS_HISTORY:
            try:
