# ==========================================
# ARCHIVO: rag/embeddings.py
# ==========================================
"""
Módulo de embeddings y vector store (RAG).
Usa sentence-transformers + FAISS (todo local y gratis).
"""

import os
from typing import List, Optional
from pathlib import Path

# Lazy imports para que la app arranque rápido aunque no se use RAG todavía
_embeddings = None
_vectorstore = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"}
        )
    return _embeddings


def build_vectorstore_from_texts(texts: List[str], metadatas: Optional[List[dict]] = None):
    """Crea un FAISS vectorstore a partir de textos."""
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    docs = []
    for i, text in enumerate(texts):
        meta = metadatas[i] if metadatas else {"source": f"doc_{i}"}
        docs.append(Document(page_content=text, metadata=meta))

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore


def load_or_create_vectorstore(persist_dir: str = "data/faiss_index"):
    """Carga el vectorstore si existe, si no devuelve None."""
    from langchain_community.vectorstores import FAISS

    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        embeddings = get_embeddings()
        return FAISS.load_local(
            persist_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )
    return None


def save_vectorstore(vectorstore, persist_dir: str = "data/faiss_index"):
    """Guarda el vectorstore en disco."""
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(persist_dir)
