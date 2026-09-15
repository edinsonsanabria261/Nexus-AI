import streamlit as st
import uuid
from groq import Groq
from openai import OpenAI
from anthropic import Anthropic
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge
from tools.file_processor import process_and_index_file
from tools.history_manager import save_chat_message, get_unique_sessions, load_session_messages

# Configuración de página limpia
st.set_page_config(
    page_title=config.BOT_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección estricta de CSS para evitar parpadeos y mantener el modo oscuro empresarial
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
    # Inicialización de identificadores únicos para hilos persistentes en Supabase
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = str(uuid.uuid4())
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = "Nueva investigación"
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nEntorno táctico multi-modelo con historial persistente en Supabase.\n\nPuedes enseñarme con:\n`recuerda esto: [texto]`\n\n¿En qué puedo ayudarte?"
        }]
    if "use_web_search" not in st.session_state:
        st.session_state.use_web_search = True
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = "Groq (Llama 3)"

def generate_response(question, provider):
    q_lower = question.lower().strip()
    
    # Procesar comando manual de aprendizaje externo
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"🧠 **Guardado en memoria persistente con éxito:**\n\n> {knowledge}"
            return "❌ Error al intentar conectar o guardar en Supabase."
        return "⚠️ Por favor, escribe información válida después del comando `recuerda esto:`"

    # 1. Búsqueda semántica vectorizada (RAG)
    memory_hits = search_knowledge(question, limit=5)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join([f"- {m['content']}" for m in memory_hits])

    # 2. Inteligencia web (OSINT)
    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("🔍 Rastreando fuentes web actualizadas..."):
            try:
                web_text = search_and_read(question, max_results=3, read_full=True)
            except Exception:
                web_text = ""

    # 3. Consolidación de Prompt Dinámico
    custom_system_prompt = config.SYSTEM_PROMPT
    if memory_text or web_text:
        custom_system_prompt += "\n\n[CONTEXTO EXTRACTO Y ACTUALIZADO DE TU ENTORNO]"
        if memory_text:
            custom_system_prompt += f"\n- Datos recuperados de tu memoria persistente (documentos/manuales):\n{memory_text}"
        if web_text:
            custom_system_prompt += f"\n- Inteligencia en tiempo real de internet:\n{web_text}"
        custom_system_prompt += "\nUtiliza este contexto únicamente si guarda relación con la pregunta. Cita fuentes si aplica."

    # 4. Enrutamiento dinámico hacia API seleccionada
    try:
        if provider == "OpenAI (GPT-4o)":
            if not config.OPENAI_API_KEY:
                return "❌ Error: Falta 'OPENAI_API_KEY' en tu panel de variables de Render para usar GPT-4o."
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            messages = [{"role": "system", "content": custom_system_prompt}]
            for msg in st.session_state.messages[-6:]:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            res = client.chat.completions.create(model=config.MODEL_OPENAI, messages=messages, temperature=0.25)
            return res.choices[0].message.content

        elif provider == "Anthropic (Claude 3.5 Sonnet)":
            if not config.ANTHROPIC_API_KEY:
                return "❌ Error: Falta 'ANTHROPIC_API_KEY' en tu panel de variables de Render para usar Claude 3.5."
            client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            messages = []
            for msg in st.session_state.messages[-6:]:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            res = client.messages.create(model=config.MODEL_ANTHROPIC, max_tokens=2500, temperature=0.25, system=custom_system_prompt, messages=messages)
            return res.content[0].text

        else:  # Groq por defecto
            if not config.GROQ_API_KEY:
                return "❌ Error: Falta configurar la variable 'GROQ_API_KEY' en Render."
            client = Groq(api_key=config.GROQ_API_KEY)
            messages = [{"role": "system", "content": custom_system_prompt}]
            for msg in st.session_state.messages[-6:]:
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            res = client.chat.completions.create(model=config.MODEL_GROQ, messages=messages, temperature=0.25)
            return res.choices[0].message.content
    except Exception as e:
        return f"❌ Error en la llamada al modelo ({provider}): {e}"

def main():
    init_session_state()

    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.9rem;">🛡️</div>
        <div>
            <h1>{config.BOT_NAME}</h1>
            <p>Asistente de Ciberseguridad Experto · Entorno Avanzado Multi-Modelo</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### ⚡ Panel de Control")
        st.caption("NexusSec Artificial Intelligence")
        st.divider()

        if st.button("🔄 Nueva conversación", use_container_width=True):
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.chat_title = "Nueva investigación"
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Nueva conversación iniciada. Historial reseteado para este hilo operativo."
            }]
            st.rerun()

        st.divider()
        st.session_state.use_web_search = st.toggle("🌐 Módulo OSINT / Web Search", value=st.session_state.use_web_search)

        # COMPONENTE FASE B: Selector dinámico de motores LLM
        st.divider()
        st.markdown("### 🧠 Motor de Inteligencia (LLM)")
        provider_options = ["Groq (Llama 3)", "OpenAI (GPT-4o)", "Anthropic (Claude 3.5 Sonnet)"]
        st.session_state.selected_provider = st.selectbox(
            "Cerebro activo:",
            options=provider_options,
            index=provider_options.index(st.session_state.selected_provider),
            label_visibility="collapsed"
        )

        # COMPONENTE FASE A: Analizador Multiformato Expandido (PDF, Word, Excel, Código)
        st.divider()
        st.markdown("### 📁 Analizador Multimodal")
        st.caption("Sube PDFs, Word (.docx), Excel (.xlsx), código o notas")
        uploaded_file = st.file_uploader(
            "Cargar archivo para indexar", 
            type=["pdf", "txt", "py", "js", "json", "md", "docx", "doc", "xlsx"],
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
            if file_key not in st.session_state:
                with st.spinner(f"Indexando semánticamente {uploaded_file.name}..."):
                    file_bytes = uploaded_file.read()
                    chunks_saved = process_and_index_file(file_bytes, uploaded_file.name)
                    
                    if chunks_saved > 0:
                        st.success(f"✅ ¡{uploaded_file.name} procesado! {chunks_saved} bloques indexados.")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"⚙️ **Sistema:** El archivo `{uploaded_file.name}` ha sido fragmentado en {chunks_saved} bloques semánticos dentro de Supabase. Ya puedes consultarme sobre su contenido."
                        })
                    else:
                        st.error("❌ No se pudo extraer texto. Verifica el formato o codificación.")
