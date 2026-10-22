"""Memoria de conocimiento en Supabase (auto-aprendizaje)."""

import os
import re

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


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
    if not content or not content.strip():
        return False
    data = {"content": content.strip()[:8000], "source": source}
    if tags:
        data["tags"] = tags[:200]
    try:
        client.table("knowledge").insert(data).execute()
        return True
    except Exception as exc:
        print(f"[memory] Error al guardar: {type(exc).__name__}: {exc}")
        return False


def search_knowledge(query: str, limit: int = 6) -> list:
    """Búsqueda por texto. Intenta términos clave si la query completa no da resultados."""
    client = get_supabase()
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

    hits = _run(query.strip()[:120])
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
        f"P: {question.strip()[:300]}\n"
        f"R: {answer.strip()[:1500]}"
    )
    return save_knowledge(snippet, source="auto", tags="auto")
