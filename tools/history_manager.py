"""Historial de conversaciones en Supabase."""

from tools.memory import get_supabase


def save_chat_message(session_id: str, title: str, role: str, content: str) -> None:
    client = get_supabase()
    if not client or not content or not str(content).strip():
        return
    try:
        client.table("chat_history").insert(
            {
                "session_id": str(session_id),
                "title": str(title)[:40],
                "role": str(role),
                "content": str(content),
            }
        ).execute()
    except Exception as exc:
        print(f"[history] Error al guardar: {exc}")


def get_unique_sessions() -> list:
    client = get_supabase()
    if not client:
        return []
    try:
        response = (
            client.table("chat_history")
            .select("session_id, title, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        seen = set()
        unique = []
        for row in response.data or []:
            session_id = row.get("session_id")
            if session_id and session_id not in seen:
                seen.add(session_id)
                unique.append(row)
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
