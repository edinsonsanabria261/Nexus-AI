# ==========================================
# ARCHIVO: tools/web_search.py
# ==========================================
"""
Herramienta de búsqueda web optimizada usando DuckDuckGo.
Diseñada para OSINT y recolección de contexto en tiempo real sin bloqueos.
"""

from duckduckgo_search import DDGS
from typing import List, Dict
import html2text
import requests
import time


def search_web(query: str, max_results: int = 5) -> List[Dict]:
    """
    Busca en la web usando DuckDuckGo (sin API key).
    Devuelve lista de resultados estructurados.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                query,
                max_results=max_results,
                region="wt-wt",  # Global
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
        print(f"[web_search] Error en el motor DuckDuckGo: {e}")
        return []


def fetch_page_content(url: str, max_chars: int = 4000) -> str:
    """
    Descarga y limpia de forma segura el contenido de una página web,
    evitando bloqueos (Cloudflare/403) y controlando el consumo de memoria RAM.
    """
    try:
        # User-Agent realista de navegador comercial para evitar bloqueos directos 403
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
        }
        
        # Realizamos la petición por flujo (stream) para poder validar el tipo de archivo antes de descargarlo entero
        with requests.get(url, headers=headers, timeout=8, stream=True) as resp:
            resp.raise_for_status()
            
            # 1. Protección de Memoria: Evitar descargar PDFs masivos o binarios ejecutables
            content_type = resp.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type and 'text/plain' not in content_type:
                return f"[La página no es un documento de texto plano procesable: {content_type}]"
                
            # 2. Forzar la codificación de caracteres nativa declarada por el servidor web
            if resp.encoding is None or resp.encoding == 'ISO-8859-1':
                resp.encoding = resp.apparent_encoding
                
            # Leemos el contenido de forma segura hasta el límite establecido
            html_content = resp.text

        # Configuración avanzada de limpieza HTML a Markdown/Texto plano
        h = html2text.HTML2Text()
        h.ignore_links = True  # Cambiado a True para evitar inyectar URLs repetitivas al LLM
        h.ignore_images = True
        h.ignore_emphasis = True
        h.body_width = 0
        
        text = h.handle(html_content)

        # Normalización sintáctica del texto (eliminación de saltos de línea basura)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean = "\n".join(lines)

        return clean[:max_chars]
    except requests.exceptions.Timeout:
        return "[Error: Tiempo de espera agotado al conectar con el servidor objetivo]"
    except requests.exceptions.HTTPError as http_err:
        return f"[Acceso denegado o error del servidor: Código {http_err.response.status_code}]"
    except Exception as e:
        return f"[No se pudo leer la página: {str(e)[:80]}]"


def search_and_read(query: str, max_results: int = 3, read_full: bool = True) -> str:
    """
    Busca en la web y extrae el texto profundo de las páginas de mayor relevancia.
    Estructura la información de forma óptima para su inserción en el System Prompt.
    """
    results = search_web(query, max_results=max_results)
    
    if not results:
        return "No se encontraron resultados relevantes en la red para esta consulta."

    context_parts = []
    context_parts.append(f"### INFORMACIÓN OSINT RECOLECTADA EN TIEMPO REAL PARA: '{query}'\n")

    for i, r in enumerate(results, 1):
        part = f"FUENTE #{i}: {r['title']}\n"
        part += f"ENLACE PÚBLICO: {r['url']}\n"
        part += f"EXTRACTO INICIAL: {r['snippet']}\n"

        # Leemos el contenido completo solo de las 2 fuentes más críticas
        if read_full and i <= 2:
            content = fetch_page_content(r["url"], max_chars=2000)
            if content and not content.startswith("["):
                part += f"DETALLES ADICIONALES DEL SITIO:\n{content}\n"

        context_parts.append(part)
        time.sleep(0.4)  # Retardo táctico de cortesía para mitigar bloqueos por ráfagas (rate-limiting)

    return "\n=========================================\n".join(context_parts)
