import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge

st.set_page_config(
    page_title=config.BOT_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS seguro y con buen contraste
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
        return "Falta GROQ_API_KEY en Render."

    q_lower = question.lower().strip()
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"Guardado en memoria persistente:\n\n> {knowledge}"
            return "Error al guardar en Supabase. Revisa la conexion."
        return "Escribe algo despues de 'recuerda esto:'"

    memory_hits = search_knowledge(question, limit=4)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join([f"- {m['content']}" for m in memory_hits])

    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("Buscando informacion..."):
            web_text = search_and_read(question, max_results=3, read_full=True)

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
            temperature=0.35,
            max_tokens=2500
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


def main():
    init_session_state()

    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 1.9rem;">🛡️</div>
        <div>
            <h1>{config.BOT_NAME}</h1>
            <p>Asistente de Ciberseguridad · Memoria Persistente</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"### {config.BOT_NAME}")
        st.caption("Ciberseguridad avanzada")
        st.divider()

        if st.button("Nueva conversacion", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "Nueva conversacion iniciada. ¿En que puedo ayudarte?"
            }]
            st.rerun()

        st.divider()
        st.session_state.use_web_search = st.toggle("Buscar en la web", value=st.session_state.use_web_search)

        st.divider()
        st.markdown("**Modelo**")
        st.code(config.GROQ_MODEL, language=None)

        st.divider()
        st.markdown("**Aprender**")
        st.code("recuerda esto: tu texto", language=None)

        st.divider()
        st.caption(f"v0.3 · {datetime.now().strftime('%Y-%m-%d')}")
        st.caption(f"Creado por {config.OWNER_NAME}")

    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

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
