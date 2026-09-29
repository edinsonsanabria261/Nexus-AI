"""
Herramientas de ciberseguridad para NexusSec AI
"""

import hashlib
import socket
import requests
from urllib.parse import urlparse

# Timeout general
TIMEOUT = 8


def tool_cve(cve_id: str) -> str:
    """Busca información de un CVE."""
    cve_id = cve_id.strip().upper()
    if not cve_id.startswith("CVE-"):
        cve_id = f"CVE-{cve_id}"

    try:
        # API pública de CIRCL
        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return f"No se encontró información para **{cve_id}**."

        data = r.json()
        summary = data.get("summary") or data.get("descriptions", [{}])[0].get("value", "Sin descripción")
        cvss = data.get("cvss") or data.get("cvss3", "N/A")
        published = data.get("Published") or data.get("published", "N/A")
        references = data.get("references", [])[:3]

        refs_text = "\n".join([f"- {ref}" for ref in references]) if references else "Sin referencias"

        return (
            f"### {cve_id}\n\n"
            f"**Resumen:** {summary}\n\n"
            f"**CVSS:** {cvss}\n"
            f"**Publicado:** {published}\n\n"
            f"**Referencias:**\n{refs_text}"
        )
    except Exception as e:
        return f"Error al consultar CVE: {e}"


def tool_whois(domain: str) -> str:
    """Información básica de un dominio (whois simplificado)."""
    domain = domain.strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
    try:
        # Usamos una API pública sencilla
        url = f"https://api.whois.vu/?q={domain}"
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return f"No se pudo obtener WHOIS de **{domain}**."

        data = r.json()
        return (
            f"### WHOIS → {domain}\n\n"
            f"- **Disponible:** {data.get('available', 'N/A')}\n"
            f"- **Registrado:** {data.get('created', 'N/A')}\n"
            f"- **Expira:** {data.get('expires', 'N/A')}\n"
            f"- **Registrante:** {data.get('registrar', 'N/A')}\n"
            f"- **DNS:** {', '.join(data.get('ns', [])) if data.get('ns') else 'N/A'}"
        )
    except Exception as e:
        return f"Error en WHOIS: {e}"


def tool_dns(domain: str) -> str:
    """Registros DNS básicos."""
    domain = domain.strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
    results = []

    try:
        # A
        try:
            ips = socket.getaddrinfo(domain, None)
            a_records = list({item[4][0] for item in ips})
            results.append(f"**A:** {', '.join(a_records)}")
        except Exception:
            results.append("**A:** No encontrado")

        # Usamos Google DNS API para más registros
        for rtype in ["MX", "NS", "TXT"]:
            try:
                url = f"https://dns.google/resolve?name={domain}&type={rtype}"
                r = requests.get(url, timeout=TIMEOUT)
                data = r.json()
                answers = data.get("Answer", [])
                if answers:
                    values = [ans.get("data", "") for ans in answers]
                    results.append(f"**{rtype}:** {', '.join(values)}")
                else:
                    results.append(f"**{rtype}:** No encontrado")
            except Exception:
                results.append(f"**{rtype}:** Error")

        return f"### DNS → {domain}\n\n" + "\n".join(results)
    except Exception as e:
        return f"Error en DNS: {e}"


def tool_ip(ip: str) -> str:
    """Información de una IP."""
    ip = ip.strip()
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,query,mobile,proxy,hosting"
        r = requests.get(url, timeout=TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            return f"No se pudo obtener información de **{ip}**."

        return (
            f"### IP → {data.get('query')}\n\n"
            f"- **País:** {data.get('country')} ({data.get('regionName')})\n"
            f"- **Ciudad:** {data.get('city')}\n"
            f"- **ISP:** {data.get('isp')}\n"
            f"- **Organización:** {data.get('org')}\n"
            f"- **AS:** {data.get('as')}\n"
            f"- **Proxy/VPN:** {data.get('proxy')}\n"
            f"- **Hosting:** {data.get('hosting')}"
        )
    except Exception as e:
        return f"Error al consultar IP: {e}"


def tool_headers(url: str) -> str:
    """Analiza cabeceras de seguridad de una URL."""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
        headers = r.headers

        security_headers = {
            "Strict-Transport-Security": headers.get("Strict-Transport-Security", "❌ No presente"),
            "Content-Security-Policy": headers.get("Content-Security-Policy", "❌ No presente"),
            "X-Frame-Options": headers.get("X-Frame-Options", "❌ No presente"),
            "X-Content-Type-Options": headers.get("X-Content-Type-Options", "❌ No presente"),
            "Referrer-Policy": headers.get("Referrer-Policy", "❌ No presente"),
            "Permissions-Policy": headers.get("Permissions-Policy", "❌ No presente"),
            "Server": headers.get("Server", "N/A"),
        }

        lines = [f"### Headers de seguridad → {url}\n"]
        for k, v in security_headers.items():
            lines.append(f"- **{k}:** {v}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error al obtener headers: {e}"


def tool_hash(text: str) -> str:
    """Calcula hashes de un texto."""
    text = text.strip()
    if not text:
        return "Debes proporcionar un texto para hashear."

    md5 = hashlib.md5(text.encode()).hexdigest()
    sha1 = hashlib.sha1(text.encode()).hexdigest()
    sha256 = hashlib.sha256(text.encode()).hexdigest()
    sha512 = hashlib.sha512(text.encode()).hexdigest()

    return (
        f"### Hashes\n\n"
        f"**Texto:** `{text[:80]}{'...' if len(text) > 80 else ''}`\n\n"
        f"- **MD5:** `{md5}`\n"
        f"- **SHA1:** `{sha1}`\n"
        f"- **SHA256:** `{sha256}`\n"
        f"- **SHA512:** `{sha512}`"
    )


def detect_and_run_tool(user_input: str) -> str | None:
    """
    Detecta si el usuario quiere usar una herramienta y la ejecuta.
    Devuelve el resultado o None si no es un comando de herramienta.
    """
    text = user_input.strip()
    lower = text.lower()

    if lower.startswith("cve "):
        return tool_cve(text[4:].strip())
    if lower.startswith("whois "):
        return tool_whois(text[6:].strip())
    if lower.startswith("dns "):
        return tool_dns(text[4:].strip())
    if lower.startswith("ip "):
        return tool_ip(text[3:].strip())
    if lower.startswith("headers "):
        return tool_headers(text[8:].strip())
    if lower.startswith("hash "):
        return tool_hash(text[5:].strip())

    return None
