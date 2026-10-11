"""Búsqueda web por modo: texto, noticias, imágenes, videos, libros y finanzas."""

import time

import html2text
import requests
from duckduckgo_search import DDGS


def _call(kind: str, query: str, max_results: int) -> list:
    try:
        with DDGS() as ddgs:
            method = getattr(ddgs, kind, None)
            if method is None:
                return []
            try:
                raw = method(query, max_results=max_results, safesearch="moderate")
            except TypeError:
                raw = method(query, max_results=max_results)
            return list(raw)
    except Exception as exc:
        print(f"[web_search] {kind} falló: {exc}")
        return []


def _link(item: dict) -> str:
    for key in ("href", "url", "content"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    return ""


def _cards_from(items: list) -> list:
    cards = []
    for item in items:
        title = item.get("title") or item.get("name") or "Sin título"
        url = _link(item)
        snippet = item.get("body") or item.get("snippet") or item.get("description") or item.get("info") or ""
        source = item.get("source") or item.get("publisher") or item.get("author") or ""
        if not title and not url:
            continue
        cards.append(
            {
                "title": str(title).strip(),
                "url": url,
                "snippet": str(snippet).strip()[:500],
                "source": str(source).strip(),
            }
        )
    return cards


def search_cards(query: str, mode: str = "todo", max_results: int = 4) -> list:
    if mode == "noticias" or mode == "finanzas":
        cards = _cards_from(_call("news", query, max_results))
        return cards or _cards_from(_call("text", query, max_results))
    if mode == "imagenes":
        cards = _cards_from(_call("images", query, max_results))
        return cards or _cards_from(_call("text", query + " imagen", max_results))
    if mode == "videos":
        cards = _cards_from(_call("videos", query, max_results))
        return cards or _cards_from(_call("text", query + " video", max_results))
    if mode == "libros":
        cards = _cards_from(_call("books", query, max_results))
        return cards or _cards_from(_call("text", query + " libro", max_results))
    return _cards_from(_call("text", query, max_results))


def fetch_page_content(url: str, max_chars: int = 2000) -> str:
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        with requests.get(url, headers=headers, timeout=8, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ""
            if response.encoding is None or response.encoding == "ISO-8859-1":
                response.encoding = response.apparent_encoding
            html = response.text
        parser = html2text.HTML2Text()
        parser.ignore_links = True
        parser.ignore_images = True
        parser.ignore_emphasis = True
        parser.body_width = 0
        lines = [line.strip() for line in parser.handle(html).splitlines() if line.strip()]
        return "\n".join(lines)[:max_chars]
    except Exception:
        return ""


def _preview(cards: list) -> str:
    lines = []
    for card in cards[:6]:
        source = f" · {card['source']}" if card["source"] else ""
        if card["url"]:
            lines.append(f"- [{card['title']}]({card['url']}){source}")
        else:
            lines.append(f"- {card['title']}{source}")
    return "\n".join(lines)


def _context(cards: list, read_pages: bool) -> str:
    parts = []
    for index, card in enumerate(cards, start=1):
        block = f"FUENTE {index}: {card['title']}\nENLACE: {card['url']}\nNOTA: {card['snippet']}"
        if read_pages and index <= 2 and card["url"]:
            page = fetch_page_content(card["url"])
            if page:
                block += f"\nEXTRACTO:\n{page}"
            time.sleep(0.3)
        parts.append(block)
    return "\n\n".join(parts)


def gather(query: str, mode: str = "todo", read_pages: bool = False, max_results: int = 4):
    """Devuelve (contexto para el modelo, lista corta para mostrar)."""
    cards = search_cards(query, mode=mode, max_results=max_results)
    if not cards:
        return "", ""
    return _context(cards, read_pages=read_pages), _preview(cards)


def search_and_read(query: str, max_results: int = 3, read_full: bool = True) -> str:
    context, _preview_text = gather(query, mode="todo", read_pages=read_full, max_results=max_results)
    return context or "No se encontraron resultados."
