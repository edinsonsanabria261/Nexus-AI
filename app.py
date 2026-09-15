import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge

st.set_page_config(
    page_title=f"{config.BOT_NAME}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS + HTML Diseño Mejorado ==========
st.markdown("""
<style>
    /* ========== Fondo y base ========== */
    .stApp {
        background-color: #0f0f0f;
        color: #e8eaed;
    }

    /* ========== Sidebar ========== */
    section[data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: 1px solid #2d2d2d;
        transition: all 0.3s ease;
    }
    section[data-testid="stSidebar"] * {
        color: #e8eaed !important;
    }

    /* ========== Header con animación ========== */
    .main-header {
        background: linear-gradient(90deg, #1a1a1a, #252525);
        padding: 1.2rem 1.6rem;
        border-radius: 16px;
        border: 1px solid #333;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 14px;
        animation: fadeInDown 0.5s ease-out;
        transition: all 0.3s ease;
    }
    .main-header:hover {
        border-color: #444;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #f1f3f4;
    }
    .main-header p {
        margin: 0;
        font-size: 0.85rem;
        color: #9aa0a6;
    }

    /* ========== Mensajes del chat ========== */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 0.6rem 0 !important;
        animation: fadeInUp 0.35s ease-out;
        transition: all 0.25s ease;
    }
    div[data-testid="stChatMessage"]:hover {
        transform: translateX(4px);
    }

    /* ========== Input estilo cápsula ========== */
    .stChatInput {
        border-radius: 28px !important;
        transition: all 0.3s ease;
    }
    .stChatInput:focus-within {
        box-shadow: 0 0 0 2px rgba(138, 180, 248, 0.3);
    }
    .stChatInput textarea {
        border-radius: 28px !important;
        padding-left: 18px !important;
        transition: all 0.3s ease;
    }

    /* ========== Botones con animación ========== */
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid #3c4043 !important;
        background-color: #2d2d2d !important;
        color: #e8eaed !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .stButton > button:hover {
        background-color: #3c4043 !important;
        border-color: #5f6368 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ========== Código ========== */
    code {
        background-color: #2d2d2d !important;
st.markdown("""
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
""", unsafe_allow_html=True)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nAsistente de ciberseguridad con **memoria persistente**.\n\nPuedes enseñarme con:\n`recuerda esto: [texto]`\n\n¿En qué puedo ayudarte?"
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
        return "⚠️ Falta GROQ_API_KEY en Render."

    # Comando de memoria
    q_lower = question.lower().strip()
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"✅ **Guardado en memoria persistente:**\n\n> {knowledge}"
            return "❌ Error al guardar en Supabase. Revisa la conexión."
        return "Escribe algo después de `recuerda esto:`"

    # Buscar en memoria
    memory_hits = search_knowledge(question, limit=4)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join([f"- {m['content']}" for m in memory_hits])

    # Búsqueda web
    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("🔍 Buscando información actualizada..."):
            web_text = search_and_read(question, max_results=3, read_full=True)

    # Construir mensajes
    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    for msg in st.session_state.messages[-6:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    extra = ""
    if memory_text:
        extra += f"\n\n### Conocimiento guardado:\n{memory_text}"
    if web_text:
        extra += f"\n\n### Información de la web:\n{web_text}"

    final_q = question if not extra else f"{question}\n{extra}"
    messages.append({"role": "user", "content": final_q})

    try:
        res = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.35,
            max_tokens=2500
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"


def main():
    init_session_state()

    # Header
    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.9rem;">🛡️</div>
        <div>
            <h1>{config.BOT_NAME}</h1>
            <p>Asistente de Ciberseguridad · Memoria Persistente</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 🛡️ NexusSec AI")
        st.caption("Ciberseguridad avanzada")

        st.divider()
        if st.button("＋ Nueva conversación", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Nueva conversación iniciada. ¿En qué puedo ayudarte?"
            }]
            st.rerun()

        st.divider()
        st.markdown("**Herramientas**")
        st.session_state.use_web_search = st.toggle("🔍 Buscar en la web", value=st.session_state.use_web_search)

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)

        st.divider()
        st.markdown("**Aprender**")
        st.code("recuerda esto: tu texto", language=None)

        st.divider()
        st.caption(f"v0.3 · {datetime.now().strftime('%Y-%m-%d')}")
        st.caption(f"Creado por {config.OWNER_NAME}")

    # Chat
    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input(f"Pregunta a {config.BOT_NAME}..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🛡️"):
            response = generate_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
