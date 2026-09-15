"""
Memoria persistente usando Supabase
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[memory] Faltan SUPABASE_URL o SUPABASE_KEY")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[memory] Error creando cliente: {e}")
        return None


def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
    sb = get_supabase()
    if not sb:
        return False
    try:
        data = {
            "content": content,
            "source": source
        }
        # Solo agregamos tags si la columna existe
        if tags:
            data["tags"] = tags

        result = sb.table("knowledge").insert(data).execute()
        print(f"[memory] Guardado exitoso: {result}")
        return True
    except Exception as e:
        print(f"[memory] Error guardando: {type(e).__name__}: {e}")
        return False


def search_knowledge(query: str, limit: int = 5) -> list:
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = (
            sb.table("knowledge")
            .select("content, source, created_at")
            .ilike("content", f"%{query}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[memory] Error buscando: {e}")
        return []


def get_recent_knowledge(limit: int = 8) -> list:
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = (
            sb.table("knowledge")
            .select("content, source, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[memory] Error obteniendo recientes: {e}")
        return []
