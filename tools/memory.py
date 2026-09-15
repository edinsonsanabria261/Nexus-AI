"""
Memoria persistente semántica (RAG) optimizada para Supabase usando API Externa Gratuita
"""

import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Usamos la API pública y gratuita de HuggingFace para generar vectores de 384 dimensiones al instante
API_URL = "https://huggingface.co"

def obtener_embedding_externo(texto: str) -> list:
    """Llama a la API externa gratuita para convertir el texto en un vector numérico."""
    try:
        # Petición directa sin necesidad de keys obligatorias para este modelo público
        response = requests.post(API_URL, json={"inputs": texto}, timeout=10)
        if response.status_code == 200:
            raw_vector = response.json()
            # Forzamos que cada elemento sea un float puro para PostgreSQL
            return [float(x) for x in raw_vector]
        else:
            print(f"[memory] Error en API externa: Código {response.status_code}")
            return []
    except Exception as e:
        print(f"[memory] Error generando embedding externo: {e}")
        return []

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[memory] Configuración incompleta: Faltan SUPABASE_URL o SUPABASE_KEY")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"[memory] Error crítico al enlazar el cliente Supabase: {e}")
        return None

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
        print("[memory] Conocimiento indexado vectorialmente de forma exitosa.")
        return True
    except Exception as e:
        print(f"[memory] Fallo al guardar en la base de datos: {type(e).__name__}: {e}")
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
    except Exception as e:
        print(f"[memory] Error ejecutando la búsqueda semántica vectorizada: {e}")
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
        print(f"[memory] Error recuperando logs recientes: {e}")
        return []
