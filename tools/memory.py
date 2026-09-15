"""
Memoria persistente usando Supabase
"""

import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[memory] Error conectando a Supabase: {e}")
        return None


def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
    """Guarda un conocimiento en la base de datos."""
    sb = get_supabase()
    if not sb:
        return False
    try:
        sb.table("knowledge").insert({
            "content": content,
            "source": source,
            "tags": tags
        }).execute()
        return True
    except Exception as e:
        print(f"[memory] Error guardando: {e}")
        return False


def search_knowledge(query: str, limit: int = 5) -> list[dict]:
    """
    Busca conocimientos relevantes.
    Por ahora hace una búsqueda simple por texto.
    Más adelante se puede mejorar con embeddings.
    """
    sb = get_supabase()
    if not sb:
        return []
    try:
        # Búsqueda simple (ilike)
        response = sb.table("knowledge")\
            .select("content, source, tags, created_at")\
            .ilike("content", f"%{query}%")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return response.data or []
    except Exception as e:
        print(f"[memory] Error buscando: {e}")
        return []


def get_recent_knowledge(limit: int = 8) -> list[dict]:
    """Obtiene los conocimientos más recientes."""
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = sb.table("knowledge")\
            .select("content, source, tags, created_at")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return response.data or []
    except Exception as e:
        print(f"[memory] Error obteniendo recientes: {e}")
        return []
