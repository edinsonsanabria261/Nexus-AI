"""Historial de conversaciones en Supabase."""

from tools.memory import get_supabase


def save_chat_message(session_id: str, title: str, role: str, content: str) -> bool:
    client = get_supabase()
    if not client or not content or not str(content).strip():
        return False
    try:
        client.table("chat_history").insert(
            {
                "session_id": str(session_id),
                "title": (str(title) or "Nueva conversación")[:80],
                "role": str(role),
                "content": str(content),
            }
        ).execute()
        return True
    except Exception as exc:
        print(f"[history] Error al guardar: {exc}")
        return False


def get_unique_sessions(limit: int = 40) -> list:
    """Lista conversaciones únicas, la más reciente primero. Nunca borra historial."""
    client = get_supabase()
    if not client:
        return []
    try:
        response = (
            client.table("chat_history")
            .select("session_id, title, created_at")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        seen = set()
        unique = []
        for row in response.data or []:
            session_id = row.get("session_id")
            if not session_id or session_id in seen:
                continue
            seen.add(session_id)
            title = (row.get("title") or "Sin título").strip() or "Sin título"
            unique.append(
                {
                    "session_id": session_id,
                    "title": title[:80],
                    "created_at": row.get("created_at"),
                }
            )
            if len(unique) >= limit:
                break
        return unique
    except Exception as exc:
        print(f"[history] Error al listar: {exc}")
        return []


def load_session_messages(session_id: str) -> list:
    client = get_supabase()
    if not client:
        return []
    try:
        response = (
            client.table("chat_history")
            .select("role, content")
            .eq("session_id", str(session_id))
            .order("created_at", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        print(f"[history] Error al cargar: {exc}")
        return []


def rename_session(session_id: str, new_title: str) -> bool:
    """Renombra una conversación actualizando el título en todos sus mensajes."""
    client = get_supabase()
    if not client or not session_id or not new_title or not new_title.strip():
        return False
    try:
        client.table("chat_history").update(
            {"title": new_title.strip()[:80]}
        ).eq("session_id", str(session_id)).execute()
        return True
    except Exception as exc:
        print(f"[history] Error al renombrar: {exc}")
        return False
