import streamlit as st
from groq import Groq
from datetime import datetime
import config
from tools.web_search import search_and_read
from tools.memory import save_knowledge, search_knowledge

st.set_page_config(page_title=f"{config.BOT_NAME}", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.stApp {background-color:#0f0f0f; color:#e8eaed;}
section[data-testid="stSidebar"] {background-color:#1a1a1a;}
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hola, soy **{config.BOT_NAME}** 🛡️\n\nTengo memoria persistente.\nUsa: `recuerda esto: tu texto`\n\n¿En qué te ayudo?"
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
        return "Falta GROQ_API_KEY"

    # Comando de memoria
    q_lower = question.lower().strip()
    if q_lower.startswith("recuerda esto:") or q_lower.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge:
            ok = save_knowledge(knowledge, source="user", tags="manual")
            if ok:
                return f"✅ Guardado en memoria:\n\n> {knowledge}"
            return "❌ Error al guardar en Supabase"
        return "Escribe algo después de 'recuerda esto:'"

    # Buscar memoria
    memory_hits = search_knowledge(question, limit=4)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join([f"- {m['content']}" for m in memory_hits])

    # Web search
    web_text = ""
    if st.session_state.use_web_search:
        with st.spinner("Buscando..."):
            web_text = search_and_read(question, max_results=3, read_full=True)

    # Construir mensajes
    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    
    for msg in st.session_state.messages[-6:]:
        if msg["role"] in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    extra = ""
    if memory_text:
        extra += f"\n\nConocimiento guardado:\n{memory_text}"
    if web_text:
        extra += f"\n\nInfo web:\n{web_text}"

    final_question = question
    if extra:
        final_question = f"{question}\n{extra}"

    messages.append({"role": "user", "content": final_question})

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

    st.title(f"🛡️ {config.BOT_NAME}")
    st.caption("Ciberseguridad + Memoria Persistente")

    with st.sidebar:
        st.session_state.use_web_search = st.toggle("Buscar en la web", value=True)
        st.divider()
        st.code(config.GROQ_MODEL)
        if st.button("Limpiar conversación"):
            st.session_state.messages = [{"role": "assistant", "content": "Conversación reiniciada."}]
            st.rerun()
        st.caption("Comando: recuerda esto: texto")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = generate_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
