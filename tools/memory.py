"""Memoria de conocimiento en Supabase (auto-aprendizaje)."""

import os
import re

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def _sanitize_text(value: str, max_len: int = 8000) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len]


def obtener_embedding_externo(content: str):
    """Compatibilidad con flujos antiguos: aún no usamos embeddings externos."""
    return None


def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def save_knowledge(content: str, source: str = "auto", tags: str = "") -> bool:
    client = get_supabase()
    if not client:
        print("[memory] Sin conexión a Supabase")
        return False

    content = _sanitize_text(content, 8000)
    if not content or not content.strip():
        return False

    payload = {
        "content": content.strip(),
        "source": _sanitize_text(source, 200) or "auto",
    }
    if tags:
        payload["tags"] = _sanitize_text(tags, 200)

    try:
        client.table("knowledge").insert(payload).execute()
        return True
    except Exception as exc:
        print(f"[memory] Error al guardar: {type(exc).__name__}: {exc}")
        return False


def search_knowledge(query: str, limit: int = 6) -> list:
    """Búsqueda por texto. Intenta términos clave si la query completa no da resultados."""
    client = get_supabase()
    query = _sanitize_text(query, 120)
    if not client or not query or not query.strip():
        return []

    def _run(term: str) -> list:
        try:
            response = (
                client.table("knowledge")
                .select("content, source, tags, created_at")
                .ilike("content", f"%{term}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as exc:
            print(f"[memory] Error al buscar: {exc}")
            return []

    hits = _run(query.strip())
    if hits:
        return hits

    words = re.findall(r"[\wáéíóúñü-]{4,}", query.lower())
    seen = set()
    merged = []
    for word in words[:5]:
        for row in _run(word):
            key = (row.get("content") or "")[:80]
            if key and key not in seen:
                seen.add(key)
                merged.append(row)
                if len(merged) >= limit:
                    return merged
    return merged


def auto_learn(question: str, answer: str) -> bool:
    """Guarda automáticamente cada intercambio útil."""
    if not question or not answer:
        return False
    if len(answer) < 40:
        return False
    if answer.startswith("Error") or answer.startswith("Falta GROQ"):
        return False

    snippet = (
        f"P: {_sanitize_text(question, 300)}\n"
        f"R: {_sanitize_text(answer, 1500)}"
    )
    return save_knowledge(snippet, source="auto", tags="auto")
