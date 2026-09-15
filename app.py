import streamlit as st
import uuid
from groq import Groq
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge
from tools.file_processor import process_and_index_file

try:
    from tools.history_manager import save_chat_message, get_unique_sessions, load_session_messages
    HAS_HISTORY = True
except Exception:
    HAS_HISTORY = False

st.set_page_config(page_title=config.BOT_NAME, page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0d0d0d; color: #f1f3f4; }
    section[data-testid="stSidebar"] { background-color: #161616 !important; border-right: 1px solid #333333 !important; }
    section[data-testid="stSidebar"] * { color: #f1f3f4 !important; }
    .main-header { background-color: #1c1c1c; padding: 1.2rem 1.6rem; border-radius: 16px; border: 1px solid #3a3a3a; margin-bottom: 1.5rem; }
    .main-header h1 { margin: 0; font-size: 1.5rem; color: #ffffff !important; }
    .stButton > button { background-color: #2a2a2a !important; color: #ffffff !important; border-radius: 12px !important; }
    .stChatInput textarea { background-color: #1f1f1f !important; color: #ffffff !important; border-radius: 24px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
if "chat_title" not in st.session_state:
    st.session_state.chat_title = "Nueva investigación"
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nEntorno táctico listo. Sistema estable."}]
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = True
if "selected_provider" not in st.session_state:
    st.session_state.selected_provider = "Groq (Llama 3)"

def generate_response(question, provider):
    q_lower = question.lower().strip()
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge and save_knowledge(knowledge, source="user", tags="manual"):
            return f"🧠 **Guardado en memoria persistente:**\n\n> {knowledge}"
        return "❌ Error al guardar en Supabase o texto vacío."

    memory_hits = search_knowledge(question, limit=5)
    memory_text = "\n".join([f"- {m['content']}" for m in memory_hits]) if memory_hits else ""

    web_text = ""
    if st.session_state.use_web_search:
        try:
            web_text = search_and_read(question, max_results=3, read_full=True)
        except Exception:
            web_text = ""

    custom_system_prompt = config.SYSTEM_PROMPT
    if memory_text or web_text:
        custom_system_prompt += "\n\n[CONTEXTO EXTRACTO Y ACTUALIZADO]"
        if memory_text:
            custom_system_prompt += f"\n- Datos de memoria/archivos:\n{memory_text}"
        if web_text:
            custom_system_prompt += f"\n- Inteligencia web:\n{web_text}"

    try:
        if provider == "OpenAI (GPT-4o)":
            if not config.OPENAI_API_KEY: return "❌ Falta 'OPENAI_API_KEY' en Render."
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            messages = [{"role": "system", "content": custom_system_prompt}]
            for msg in st.session_state.messages[-6:]:
                if msg["role"] in ("user", "assistant"): messages.append(msg)
            messages.append({"role": "user", "content": question})
            return client.chat.completions.create(model=config.MODEL_OPENAI, messages=messages, temperature=0.25).choices[0].message.content
        elif provider == "Anthropic (Claude 3.5 Sonnet)":
            if not config.ANTHROPIC_API_KEY: return "❌ Falta 'ANTHROPIC_API_KEY' en Render."
            from anthropic import Anthropic
            client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            messages = [msg for msg in st.session_state.messages[-6:] if msg["role"] in ("user", "assistant")]
            messages.append({"role": "user", "content": question})
            return client.messages.create(model=config.MODEL_ANTHROPIC, max_tokens=2500, temperature=0.25, system=custom_system_prompt, messages=messages).content[0].text
        else:
            if not config.GROQ_API_KEY: return "❌ Falta 'GROQ_API_KEY' en Render."
            client = Groq(api_key=config.GROQ_API_KEY)
            messages = [{"role": "system", "content": custom_system_prompt}]
            for msg in st.session_state.messages[-6:]:
                if msg["role"] in ("user", "assistant"): messages.append(msg)
            messages.append({"role": "user", "content": question})
            return client.chat.completions.create(model=config.MODEL_GROQ, messages=messages, temperature=0.25).choices[0].message.content
    except Exception as e:
        return f"❌ Error en el modelo: {e}"

st.markdown(f'<div class="main-header"><h1>🛡️ {config.BOT_NAME}</h1><p>Asistente de Ciberseguridad Experto</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"### ⚡ Panel de Control")
    if st.button("🔄 Nueva conversación", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.chat_title = "Nueva investigación"
        st.session_state.messages = [{"role": "assistant", "content": "Nueva conversación iniciada."}]
        st.rerun()

    st.session_state.use_web_search = st.toggle("🌐 Módulo OSINT / Web Search", value=st.session_state.use_web_search)
    
    st.markdown("### 🧠 Motor (LLM)")
    st.session_state.selected_provider = st.selectbox("Cerebro:", ["Groq (Llama 3)", "OpenAI (GPT-4o)", "Anthropic (Claude 3.5 Sonnet)"], index=0, label_visibility="collapsed")

    st.markdown("### 📁 Analizador Multimodal")
    uploaded_file = st.file_uploader("Cargar archivo:", type=["pdf", "txt", "py", "js", "json", "md", "docx", "doc", "xlsx"], label_visibility="collapsed")
    if uploaded_file is not None:
        f_key = f"proc_{uploaded_file.name}_{uploaded_file.size}"
        if f_key not in st.session_state:
            with st.spinner("Indexando..."):
                saved = process_and_index_file(uploaded_file.read(), uploaded_file.name)
                if saved > 0:
                    st.success("✅ ¡Indexado exitoso!")
                    st.session_state.messages.append({"role": "assistant", "content": f"⚙️ **Sistema:** `{uploaded_file.name}` analizado con éxito ({saved} bloques)."})
                else:
                    st.error("❌ Archivo sin texto legible.")
            st.session_state[f_key] = True

    st.markdown("### 📜 Investigaciones")
    if HAS_HISTORY:
        try:
            past = get_unique_sessions()
            if past:
                opts = {c['title']: c['session_id'] for c in past}
                sel = st.selectbox("Historial:", options=list(opts.keys()), label_visibility="collapsed")
                t_session = opts[sel]
                if t_session != st.session_state.current_session_id:
                    st.session_state.current_session_id = t_session
                    st.session_state.chat_title = sel
                    msgs = load_session_messages(t_session)
                    if msgs: st.session_state.messages = msgs
                    st.rerun()
            else:
                st.caption("Sin hilos grabados.")
        except Exception:
            st.caption("Historial en pausa.")

    st.caption(f"v0.6 · {config.OWNER_NAME}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🛡️" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

if prompt := st.chat_input(f"Consulta..."):
    if len(st.session_state.messages) <= 1: st.session_state.chat_title = prompt[:30]
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)
    
    if HAS_HISTORY:
        try: save_chat_message(st.session_state.current_session_id, st.session_state.chat_title, "user", prompt)
        except Exception: pass

    with st.chat_message("assistant", avatar="🛡️"):
        res = generate_response(prompt, st.session_state.selected_provider)
        st.markdown(res)
    st.session_state.messages.append({"role": "assistant", "content": res})
    
    if HAS_HISTORY:
        try: save_chat_message(st.session_state.current_session_id, st.session_state.chat_title, "assistant", res)
        except Exception: pass
