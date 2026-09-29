"""
Memoria persistente semántica e historial unificados para NexusSec AI
"""

import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


# === CONOCIMIENTO (Memoria a largo plazo) ===

def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
    """Guarda conocimiento. Usa búsqueda de texto si no hay embeddings."""
    sb = get_supabase()
    if not sb or not content.strip():
        return False
    try:
        data = {
            "content": content.strip(),
            "source": source,
        }
        if tags:
            data["tags"] = tags

        sb.table("knowledge").insert(data).execute()
        return True
    except Exception as e:
        print(f"[memory] Error guardando knowledge: {e}")
        return False


def search_knowledge(query: str, limit: int = 4) -> list:
    """Busca conocimiento por texto (robusto y compatible)."""
    sb = get_supabase()
    if not sb or not query.strip():
        return []
    try:
        # Búsqueda simple y confiable por ahora
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
        print(f"[memory] Error buscando knowledge: {e}")
        return []


# === HISTORIAL DE CHATS ===

def save_chat_message(session_id: str, title: str, role: str, content: str):
    sb = get_supabase()
    if not sb or not content or not content.strip():
        return
    try:
        data = {
            "session_id": str(session_id),
            "title": str(title)[:40],
            "role": str(role),
            "content": str(content)
        }
        sb.table("chat_history").insert(data).execute()
    except Exception as e:
        print(f"[memory_history] Error: {e}")


def get_unique_sessions():
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = (
            sb.table("chat_history")
            .select("session_id, title, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        seen = set()
        unique_chats = []
        for row in (response.data or []):
            sid = row.get("session_id")
            if sid and sid not in seen:
                seen.add(sid)
                unique_chats.append(row)
        return unique_chats
    except Exception:
        return []


def load_session_messages(session_id: str):
    sb = get_supabase()
    if not sb:
        return []
    try:
        response = (
            sb.table("chat_history")
            .select("role, content")
            .eq("session_id", str(session_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except Exception:
        return []
