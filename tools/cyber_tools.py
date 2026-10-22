"""
Herramientas de ciberseguridad para NexusSec AI
"""

import hashlib
import ipaddress
import re
import socket
from urllib.parse import urlparse

import requests

# Timeout general
TIMEOUT = 8


def _normalize_domain(value: str) -> str:
    value = (value or "").strip().lower().replace("http://", "").replace("https://", "").split("/")[0]
    if not value:
        raise ValueError("Debes indicar un dominio o host válido.")
    if value.startswith(".") or value.endswith("."):
        value = value.strip(".")
    if value in {"localhost", "0.0.0.0", "127.0.0.1"} or value.endswith(".localhost"):
        raise ValueError("El dominio indicado no es seguro o no es válido.")
    if re.fullmatch(r"[a-z0-9.-]+", value) is None:
        raise ValueError("El dominio contiene caracteres no válidos.")
    return value


def _normalize_url(value: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError("Debes indicar una URL válida.")
    if not text.startswith(("http://", "https://")):
        text = "https://" + text
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    if not host or host in {"localhost", "0.0.0.0", "127.0.0.1"} or host.endswith(".localhost"):
        raise ValueError("La URL indicada no es segura o no es válida.")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise ValueError("La URL indicada apunta a un host local o no accesible.")
    except ValueError:
        pass
    return text


def tool_cve(cve_id: str) -> str:
    """Busca información de un CVE (fuente alternativa)."""
    cve_id = cve_id.strip().upper()
    if not cve_id.startswith("CVE-"):
        cve_id = f"CVE-{cve_id}"

    try:
        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()
            summary = data.get("summary", "Sin descripción")
            cvss = data.get("cvss") or data.get("cvss3") or "N/A"
            published = str(data.get("Published", data.get("published", "N/A")))[:10]
            refs = data.get("references", [])[:3]
            refs_text = "\n".join([f"- {ref}" for ref in refs]) if refs else "Sin referencias"

            if summary and summary != "Sin descripción":
                return (
                    f"### {cve_id}\n\n"
                    f"**Resumen:** {summary}\n\n"
                    f"**CVSS:** {cvss}\n"
                    f"**Publicado:** {published}\n\n"
                    f"**Referencias:**\n{refs_text}"
                )

        return (
            f"### {cve_id}\n\n"
            f"No pude obtener detalles desde las APIs públicas en este momento.\n"
            f"Puedes consultarlo manualmente en:\n"
            f"- https://nvd.nist.gov/vuln/detail/{cve_id}\n"
            f"- https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}"
        )
    except Exception as e:
        return f"Error al consultar CVE: {e}"


def tool_whois(domain: str) -> str:
    """Información básica de un dominio (whois simplificado)."""
    try:
        domain = _normalize_domain(domain)
    except ValueError as exc:
        return str(exc)

    try:
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
    try:
        domain = _normalize_domain(domain)
    except ValueError as exc:
        return str(exc)

    results = []
    try:
        try:
            ips = socket.getaddrinfo(domain, None)
            a_records = list({item[4][0] for item in ips})
            results.append(f"**A:** {', '.join(a_records)}")
        except Exception:
            results.append("**A:** No encontrado")

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
    value = (ip or "").strip()
    try:
        parsed = ipaddress.ip_address(value)
        if parsed.is_private or parsed.is_loopback or parsed.is_link_local or parsed.is_multicast or parsed.is_reserved:
            return "La IP indicada apunta a un rango privado o no accesible."
    except ValueError:
        return "Debes proporcionar una IP pública válida."

    try:
        url = f"http://ip-api.com/json/{value}?fields=status,message,country,regionName,city,isp,org,as,query,mobile,proxy,hosting"
        r = requests.get(url, timeout=TIMEOUT)
        data = r.json()

        if data.get("status") != "success":
            return f"No se pudo obtener información de **{value}**."

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
    try:
        safe_url = _normalize_url(url)
    except ValueError as exc:
        return str(exc)

    try:
        r = requests.get(safe_url, timeout=TIMEOUT, allow_redirects=True)
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

        lines = [f"### Headers de seguridad → {safe_url}\n"]
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
