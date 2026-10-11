"""Memoria de conocimiento en Supabase."""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def obtener_embedding_externo(text: str):
    """Embedding opcional. Sin OPENAI_API_KEY devuelve None y el texto igual se guarda."""
    key = os.getenv("OPENAI_API_KEY", "")
    if not key or not text or not text.strip():
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key)
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        result = client.embeddings.create(model=model, input=text[:8000])
        return result.data[0].embedding
    except Exception as exc:
        print(f"[memory] Embedding no disponible: {exc}")
        return None


def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
    client = get_supabase()
    if not client:
        print("[memory] Sin conexión a Supabase")
        return False
    if not content.strip():
        return False
    data = {"content": content.strip(), "source": source}
    if tags:
        data["tags"] = tags
    try:
        client.table("knowledge").insert(data).execute()
        return True
    except Exception as exc:
        print(f"[memory] Error al guardar: {type(exc).__name__}: {exc}")
        return False


def search_knowledge(query: str, limit: int = 4) -> list:
    client = get_supabase()
    if not client or not query.strip():
        return []
    try:
        response = (
            client.table("knowledge")
            .select("content, source, created_at")
            .ilike("content", f"%{query}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        print(f"[memory] Error al buscar: {exc}")
        return []
