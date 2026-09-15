"""
Memoria persistente semántica (RAG) optimizada para Supabase (Array Nativo)
"""

import os
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# INICIALIZACIÓN CRÍTICA: Cargamos el modelo local gratuito para generar los vectores de 384 dimensiones
print("[memory] Cargando motor local de embeddings semánticos...")
model = SentenceTransformer("all-MiniLM-L6-v2")

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
        # Generamos el vector numérico del texto y lo convertimos a una lista de floats puros
        raw_vector = model.encode(content)
        embedding_vector = [float(x) for x in raw_vector]

        data = {
            "content": content,
            "source": source,
            "embedding": embedding_vector  # Se almacena de forma nativa en Supabase
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
        # Convertimos la pregunta del chat en el mismo formato de vector numérico
        raw_vector = model.encode(query)
        query_vector = [float(x) for x in raw_vector]

        # Llamamos de manera directa a la función matemática 'match_knowledge' de la Base de Datos
        response = sb.rpc(
            "match_knowledge",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.25,  # Umbral de coincidencia conceptual
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
