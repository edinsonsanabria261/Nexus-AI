# ==========================================
# ARCHIVO: tools/web_search.py
# ==========================================
"""
Herramienta de búsqueda web gratuita usando DuckDuckGo.
Permite al chatbot aprender de la web pública en tiempo real.
"""

from duckduckgo_search import DDGS
from typing import List, Dict
import html2text
import requests
from bs4 import BeautifulSoup
import time


def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """
    Busca en la web usando DuckDuckGo (sin API key).
    Devuelve lista de resultados con título, url y snippet.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=max_results,
                region="wt-wt",  # Worldwide
                safesearch="moderate"
            ))
        
        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", "")
            })
        return formatted
    except Exception as e:
        print(f"[web_search] Error en búsqueda: {e}")
        return []


def fetch_page_content(url: str, max_chars: int = 4000) -> str:
    """
    Descarga y limpia el contenido de una página web.
    Devuelve texto plano legible.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NexusSecBot/1.0; +https://github.com/edinsonsanabria261)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # Preferimos html2text para mejor limpieza
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        text = h.handle(resp.text)

        # Limpiamos un poco
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)

        return clean[:max_chars]
    except Exception as e:
        return f"[No se pudo leer la página: {str(e)[:100]}]"


def search_and_read(query: str, max_results: int = 3, read_full: bool = True) -> str:
    """
    Busca en la web y opcionalmente lee el contenido de las páginas principales.
    Devuelve un contexto estructurado listo para el LLM.
    """
    results = search_web(query, max_results=max_results)
    
    if not results:
        return "No se encontraron resultados relevantes en la web."

    context_parts = []
    context_parts.append(f"### Resultados de búsqueda para: '{query}'\n")

    for i, r in enumerate(results, 1):
        part = f"**{i}. {r['title']}**\n"
        part += f"URL: {r['url']}\n"
        part += f"Resumen: {r['snippet']}\n"

        if read_full and i <= 2:  # Solo leemos las 2 primeras para no alargar demasiado
            content = fetch_page_content(r["url"], max_chars=2500)
            part += f"\nContenido extraído:\n{content}\n"

        context_parts.append(part)
        time.sleep(0.3)  # Cortesía

    return "\n---\n".join(context_parts)
