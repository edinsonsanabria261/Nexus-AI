"""
Gestor de historial de chats persistente en Supabase para NexusSec AI
"""

def get_supabase_client():
    """Importa dinámicamente el cliente de Supabase para evitar bloqueos."""
    try:
        import tools.memory as memory_module
        return memory_module.get_supabase()
    except Exception as e:
        print(f"[history] Error obteniendo cliente Supabase: {e}")
        return None

def save_chat_message(session_id: str, title: str, role: str, content: str):
    """Guarda un mensaje individual (usuario o asistente) en Supabase."""
    sb = get_supabase_client()
    if not sb or not content.strip():
        return
    try:
        data = {
            "session_id": session_id,
            "title": title[:40],  # Limitamos el largo del título para la barra lateral
            "role": role,
            "content": content
        }
        sb.table("chat_history").insert(data).execute()
    except Exception as e:
        print(f"[history] Error guardando mensaje: {e}")

def get_unique_sessions():
    """Recupera la lista de todas las conversaciones únicas para la barra lateral."""
    sb = get_supabase_client()
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
            if row["session_id"] not in seen:
                seen.add(row["session_id"])
                unique_chats.append(row)
        return unique_chats
    except Exception as e:
        print(f"[history] Error obteniendo sesiones: {e}")
        return []

def load_session_messages(session_id: str):
    """Carga todos los mensajes de una conversación específica."""
    sb = get_supabase_client()
    if not sb:
        return []
    try:
        response = (
            sb.table("chat_history")
            .select("role, content")
            .eq("session_id", session_id)
            .order("created_at", asc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[history] Error cargando mensajes de sesión: {e}")
        return []
