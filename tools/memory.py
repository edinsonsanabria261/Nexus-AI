"""
Memoria persistente semántica e historial unificados para NexusSec AI
"""

import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

API_URL = "https://huggingface.co"

def obtener_embedding_externo(texto: str) -> list:
    try:
        response = requests.post(API_URL, json={"inputs": texto}, timeout=10)
        if response.status_code == 200:
            raw_vector = response.json()
            return [float(x) for x in raw_vector]
        return []
    except Exception:
        return []

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

# === FUNCIONES DE CONOCIMIENTO (ARCHIVOS VECTORIALES) ===

def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
    sb = get_supabase()
    if not sb or not content.strip():
        return False
    try:
        embedding_vector = obtener_embedding_externo(content)
        if not embedding_vector:
            return False

        data = {
            "content": content,
            "source": source,
            "embedding": embedding_vector
        }
        if tags:
            data["tags"] = tags

        sb.table("knowledge").insert(data).execute()
        return True
    except Exception:
        return False

def search_knowledge(query: str, limit: int = 4) -> list:
    sb = get_supabase()
    if not sb or not query.strip():
        return []
    try:
        query_vector = obtener_embedding_externo(query)
        if not query_vector:
            return []

        response = sb.rpc(
            "match_knowledge",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.25,
                "match_count": limit
            }
        ).execute()
        
        return response.data or []
    except Exception:
        return []

# === FUNCIONES DE HISTORIAL UNIFICADAS (FASE C NATIVA) ===

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
            .order("created_at", asc=True)
            .execute()
        )
        return response.data or []
    except Exception:
        return []
