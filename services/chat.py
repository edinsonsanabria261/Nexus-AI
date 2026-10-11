"""Orquestación de una respuesta. No dibuja la interfaz."""

import config
from services.modes import MODE_HINTS, normalize_mode
from tools.cyber_tools import detect_and_run_tool
from tools.memory import save_knowledge, search_knowledge
from tools.web_search import gather


def generate_response(question: str, history: list, use_web: bool, mode: str) -> str:
    mode = normalize_mode(mode)

    tool_result = detect_and_run_tool(question)
    if tool_result:
        return tool_result

    lowered = question.lower().strip()
    if lowered.startswith("recuerda esto:") or lowered.startswith("recuerda esto :"):
        knowledge = question.split(":", 1)[1].strip()
        if knowledge and save_knowledge(knowledge, source="user", tags="manual"):
            return f"Guardado en la memoria:\n\n> {knowledge}"
        return "No se pudo guardar. Revisa SUPABASE_URL y SUPABASE_KEY."

    if not config.GROQ_API_KEY:
        return "Falta GROQ_API_KEY en el entorno."

    memory_hits = search_knowledge(question, limit=4)
    memory_text = ""
    if memory_hits:
        memory_text = "\n".join(f"- {item['content']}" for item in memory_hits if item.get("content"))

    web_context = ""
    web_preview = ""
    if use_web or mode != "todo":
        try:
            web_context, web_preview = gather(
                question,
                mode=mode,
                read_pages=(mode == "todo"),
                max_results=config.MAX_SEARCH_RESULTS,
            )
        except Exception:
            web_context = ""
            web_preview = ""

    messages = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    for msg in history[-6:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    extra = f"\n\nModo IA: {mode}. {MODE_HINTS.get(mode, '')}"
    if memory_text:
        extra += f"\n\nConocimiento guardado:\n{memory_text}"
    if web_context:
        extra += f"\n\nContexto de la web:\n{web_context}"

    messages.append({"role": "user", "content": f"{question}{extra}"})

    try:
        from groq import Groq

        client = Groq(api_key=config.GROQ_API_KEY)
        result = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.25,
            max_tokens=2500,
        )
        answer = result.choices[0].message.content or ""
    except Exception as exc:
        return f"Error en la API de Groq: {exc}"

    if web_preview:
        answer = f"{answer}\n\n---\n**Resultados rápidos**\n\n{web_preview}"
    return answer
