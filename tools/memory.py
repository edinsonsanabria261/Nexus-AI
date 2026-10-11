"""Memoria de conocimiento en Supabase (manual + auto-aprendizaje)."""

import os
import re

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Palabras que indican contenido útil de ciberseguridad para auto-guardar
CYBER_HINTS = (
    "cve", "exploit", "payload", "malware", "ransomware", "phishing",
    "pentest", "vulnerability", "vulnerabilidad", "buffer", "overflow",
    "sql injection", "xss", "rce", "lfi", "ssrf", "kerberos", "ntlm",
    "active directory", "privilege", "escalation", "lateral",
    "reverse shell", "bind shell", "nmap", "wireshark", "metasploit",
    "forense", "forensic", "hash", "encryption", "cifrado",
    "firewall", "ids", "ips", "zero-day", "0day", "bypass",
    "authentication", "autenticación", "oauth", "jwt", "api key",
    "docker", "kubernetes", "cloud", "aws", "azure", "linux",
    "windows", "powershell", "bash", "python", "shellcode",
)


def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None


def save_knowledge(content: str, source: str = "user", tags: str = "") -> bool:
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

    # Fallback: palabras significativas (>= 4 chars)
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


def looks_cyber_related(text: str) -> bool:
    lower = (text or "").lower()
    return any(h in lower for h in CYBER_HINTS)


def auto_learn(question: str, answer: str) -> bool:
    """
    Guarda automáticamente un par pregunta/respuesta si parece útil en ciberseguridad.
    No bloquea el chat si falla.
    """
    if not question or not answer:
        return False
    if len(answer) < 80:
        return False
    if answer.startswith("Error") or answer.startswith("No se pudo"):
        return False

    combined = f"{question}\n{answer}"
    if not looks_cyber_related(combined):
        return False

    # Resumen compacto para no llenar la tabla de ruido
    snippet = (
        f"P: {question.strip()[:300]}\n"
        f"R: {answer.strip()[:1500]}"
    )
    return save_knowledge(snippet, source="auto", tags="auto,ciber")
