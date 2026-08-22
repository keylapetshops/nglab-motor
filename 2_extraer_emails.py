from __future__ import annotations
"""NGLAB Motor — Paso 2: Extraer emails v4.

CAMBIO PRINCIPAL: Crawl profundo real.
En vez de adivinar rutas, entra en la home, coge TODOS los links internos
y los visita hasta encontrar el email. Así funciona independientemente de
cómo se llame la página de contacto.
"""
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import PREFIJOS_GENERICOS, DOMINIOS_BASURA, EXTENSIONES_FALSAS
from db import leads_por_estado, actualizar_lead, stats

PUPPETEER_URL = "https://email-scraper-production-1308.up.railway.app"

REGEX_EMAIL = re.compile(
    r"\b[a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,62}@"
    r"[a-zA-Z0-9][a-zA-Z0-9.\-]{0,61}[a-zA-Z0-9]"
    r"\.[a-zA-Z]{2,}\b"
)

REGEX_TELEFONO = re.compile(
    r"(?<!\d)(?:\+34[\s\-]?)?(?:6\d{2}|7[1-9]\d|8\d{2}|9\d{2})[\s\-]?\d{3}[\s\-]?\d{3}(?!\d)"
)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

DOMINIOS_TEMPORALES = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "trashmail.com", "trashmail.me",
    "maildrop.cc", "discard.email", "fakeinbox.com", "tempr.email",
    "gmail.co", "gmail.con", "gmial.com", "hotmail.co", "hotmail.con",
    "yahoo.co", "yaho.com", "outlook.co",
}

PATRONES_SOSPECHOSOS = [
    re.compile(r"noreply|no-reply|donotreply|mailer-daemon|postmaster@|wordpress@|woocommerce@|@example\.|@test\.|@domain\.", re.I),
    re.compile(r"\d{6,}@", re.I),
]

# Palabras que indican página de contacto/legal — prioridad alta
PALABRAS_PRIORITARIAS = [
    "contact", "contacto", "contactar", "contactanos",
    "aviso", "legal", "privacidad", "privacy", "rgpd", "lopd",
    "sobre", "nosotros", "quienes", "equipo", "about",
    "donde", "ubicacion", "localizacion", "llegar",
    "info", "atencion", "ayuda",
]

# Extensiones a ignorar al crawlear
EXTENSIONES_IGNORAR = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".css", ".js", ".xml", ".zip", ".doc", ".docx",
)


def _url_valida(url: str) -> str | None:
    if not url or not url.strip():
        return None
    url = url.strip()
    if url in ("/", "//", "#") or url.startswith(("javascript:", "mailto:", "tel:", "whatsapp:")):
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        return None
    if any(url.lower().endswith(ext) for ext in EXTENSIONES_IGNORAR):
        return None
    return url


def decodificar_cfemail(cf: str) -> str:
    try:
        clave = int(cf[:2], 16)
        return "".join(chr(int(cf[i:i + 2], 16) ^ clave) for i in range(2, len(cf), 2))
    except Exception:
        return ""


def es_email_valido(email: str) -> bool:
    e = email.lower().strip()
    if len(e) > 80 or e.count("@") != 1:
        return False
    local, dominio = e.split("@")
    if len(local) < 1:
        return False
    if e.endswith(EXTENSIONES_FALSAS):
        return False
    if any(basura in dominio for basura in DOMINIOS_BASURA):
        return False
    if dominio in DOMINIOS_TEMPORALES:
        return False
    if any(p.search(e) for p in PATRONES_SOSPECHOSOS):
        return False
    partes = dominio.split(".")
    if len(partes) < 2 or len(partes[-1]) < 2:
        return False
    return True


def es_email_empleado(email: str) -> bool:
    local = email.split("@")[0].lower()
    if any(local == p or local.startswith(p) for p in PREFIJOS_GENERICOS):
        return False
    if re.match(r"^[a-z]{2,}\.[a-z]{2,}$", local):
        return True
    if re.match(r"^[a-z]\.[a-z]{2,}$", local):
        return True
    return False


def desofuscar_email(texto: str) -> list[str]:
    """Detecta emails ofuscados: info[at]dominio[dot]com, info arroba dominio punto es"""
    t = texto.lower()
    t = re.sub(r'\s*\[at\]\s*|\s*\(at\)\s*|\s+at\s+|\s*\[arroba\]\s*|\s*\(arroba\)\s*|\s+arroba\s+', '@', t)
    t = re.sub(r'\s*\[dot\]\s*|\s*\(dot\)\s*|\s+dot\s+|\s*\[punto\]\s*|\s*\(punto\)\s*|\s+punto\s+', '.', t)
    emails = []
    for e in REGEX_EMAIL.findall(t):
        e = e.strip(".,;:\"'()[]").lower().replace(" ", "")
        if es_email_valido(e):
            emails.append(e)
    return emails


def extraer_emails_de_html(html: str) -> set[str]:
    """Extrae todos los emails de un HTML."""
    encontrados: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    # mailto: links
    for a in soup.select('a[href^="mailto:"]'):
        email = a["href"].removeprefix("mailto:").split("?")[0].strip()
        if email and es_email_valido(email):
            encontrados.add(email.lower())

    # Cloudflare ofuscado
    for tag in soup.select("[data-cfemail]"):
        email = decodificar_cfemail(tag["data-cfemail"])
        if email and es_email_valido(email):
            encontrados.add(email.lower())

    # Footer específico
    footer = soup.find("footer")
    if footer:
        texto_footer = footer.get_text(" ")
        for e in REGEX_EMAIL.findall(texto_footer):
            e = e.strip(".,;:\"'()[]").lower()
            if es_email_valido(e):
                encontrados.add(e)
        for e in desofuscar_email(texto_footer):
            encontrados.add(e)

    # Texto completo
    texto = soup.get_text(" ")
    for e in REGEX_EMAIL.findall(texto):
        e = e.strip(".,;:\"'()[]").lower()
        if es_email_valido(e):
            encontrados.add(e)

    # Emails ofuscados en texto completo
    for e in desofuscar_email(texto):
        encontrados.add(e)

    # HTML crudo
    for e in REGEX_EMAIL.findall(html):
        e = e.strip(".,;:\"'()[]").lower()
        if es_email_valido(e):
            encontrados.add(e)

    return encontrados


def extraer_links_internos(html: str, base_url: str, dominio_web: str) -> list[str]:
    """
    Extrae TODOS los links internos de la página.
    Prioriza los que contienen palabras clave de contacto.
    """
    soup = BeautifulSoup(html, "html.parser")
    prioritarios = []
    normales = []
    vistos = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue

        # Construir URL completa
        if href.startswith("http"):
            if dominio_web not in href:
                continue
            url_completa = href
        else:
            url_completa = urljoin(base_url, href)

        url_limpia = _url_valida(url_completa)
        if not url_limpia or url_limpia in vistos:
            continue
        vistos.add(url_limpia)

        # Clasificar por prioridad
        href_lower = href.lower()
        texto_link = (a.get_text() or "").lower().strip()
        es_prioritario = any(
            p in href_lower or p in texto_link
            for p in PALABRAS_PRIORITARIAS
        )

        if es_prioritario:
            prioritarios.append(url_limpia)
        else:
            normales.append(url_limpia)

    # Devolver prioritarios primero, luego el resto
    return prioritarios[:15] + normales[:10]


def extraer_telefonos(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    telefonos = []
    for a in soup.select('a[href^="tel:"]'):
        tel = re.sub(r"[^\d+]", "", a["href"].replace("tel:", "").strip())
        if len(tel) >= 9:
            telefonos.append(tel)
    if not telefonos:
        for t in REGEX_TELEFONO.findall(soup.get_text(" ")):
            t = re.sub(r"[^\d]", "", t)
            if len(t) >= 9:
                telefonos.append(t)
    vistos = []
    for t in telefonos:
        if t not in vistos:
            vistos.append(t)
    return vistos[:3]


def elegir_mejor(emails: set[str], dominio_web: str) -> str | None:
    if not emails:
        return None

    def puntuar(e: str) -> tuple:
        local = e.split("@")[0].lower()
        dominio = e.split("@")[1].lower()
        es_gen = any(local == p or local.startswith(p) for p in PREFIJOS_GENERICOS)
        es_prop = bool(dominio_web and dominio_web in dominio)
        es_empl = es_email_empleado(e)
        return (not (es_gen and es_prop), not es_gen, not es_prop, es_empl, len(e))

    return sorted(emails, key=puntuar)[0]


def intentar_puppeteer(url: str) -> set[str]:
    try:
        with httpx.Client(timeout=30) as c:
            r = c.post(f"{PUPPETEER_URL}/scrape", json={"url": url})
            if r.status_code == 200:
                emails = set()
                for e in r.json().get("emails", []):
                    if es_email_valido(e):
                        emails.add(e.lower())
                return emails
    except Exception:
        pass
    return set()


def procesar_lead(lead: dict, cliente: httpx.Client) -> tuple[str | None, str | None, list[str]]:
    base = lead.get("web", "")
    if not base or not base.strip():
        return None, None, []

    url_base = _url_valida(base)
    if not url_base:
        return None, None, []

    parsed = urlparse(url_base)
    dominio_web = parsed.netloc.removeprefix("www.")

    todos_emails: set[str] = set()
    todos_telefonos: list[str] = []
    mejor_fuente: str | None = None
    visitadas: set[str] = set()

    def tiene_email_bueno() -> bool:
        mejor = elegir_mejor(todos_emails, dominio_web)
        return bool(mejor and not es_email_empleado(mejor))

    def visitar(url: str) -> str | None:
        """Visita una URL y devuelve el HTML o None."""
        if url in visitadas:
            return None
        visitadas.add(url)
        try:
            r = cliente.get(url, headers={"User-Agent": UA}, timeout=8)
            if r.status_code != 200:
                return None
            if "text/html" not in r.headers.get("content-type", ""):
                return None
            return r.text
        except Exception:
            return None

    # ── FASE 1: Visitar la home ───────────────────────────────────────────────
    html_home = visitar(url_base)
    if html_home:
        todos_emails.update(extraer_emails_de_html(html_home))
        if not todos_telefonos:
            todos_telefonos = extraer_telefonos(html_home)

        if tiene_email_bueno():
            mejor_fuente = url_base
            return elegir_mejor(todos_emails, dominio_web), mejor_fuente, todos_telefonos

        # ── FASE 2: Crawl profundo — todos los links internos ─────────────────
        links = extraer_links_internos(html_home, url_base, dominio_web)

        for url in links:
            html = visitar(url)
            if not html:
                continue

            emails_antes = len(todos_emails)
            todos_emails.update(extraer_emails_de_html(html))

            if not todos_telefonos:
                todos_telefonos = extraer_telefonos(html)

            if tiene_email_bueno():
                mejor_fuente = url
                break

            time.sleep(0.15)

    # ── FASE 3: Fallback Puppeteer ────────────────────────────────────────────
    if not tiene_email_bueno():
        emails_pup = intentar_puppeteer(url_base)
        todos_emails.update(emails_pup)
        if emails_pup:
            mejor_fuente = f"{url_base} (puppeteer)"

    mejor = elegir_mejor(todos_emails, dominio_web)
    if mejor and not mejor_fuente:
        mejor_fuente = url_base

    return mejor, mejor_fuente, todos_telefonos


def main():
    # Leads SIN web → cola llamada
    sin_web = leads_por_estado("nuevo", con_web=False)
    sin_web_marcados = 0
    for lead in sin_web:
        if not lead.get("web"):
            actualizar_lead(lead["id"], estado="sin_web")
            sin_web_marcados += 1
    if sin_web_marcados:
        print(f"Sin web → cola llamada: {sin_web_marcados}")

    # Leads CON web
    pendientes = leads_por_estado("nuevo", con_web=True)
    print(f"Con web pendientes: {len(pendientes)}")

    con_email = sin_email = con_telefono = 0

    with httpx.Client(timeout=15, follow_redirects=True, max_redirects=5) as cliente:
        for i, lead in enumerate(pendientes, 1):
            nombre = lead.get("nombre_negocio", "")[:40]
            email, fuente, telefonos = procesar_lead(lead, cliente)

            campos: dict = {}
            if telefonos and not lead.get("telefono"):
                campos["telefono"] = telefonos[0]
                con_telefono += 1

            if email:
                campos.update({
                    "email": email,
                    "notas": f"Email extraído de: {fuente}",
                    "estado": "pendiente_revision",
                })
                con_email += 1
                tipo = "empleado" if es_email_empleado(email) else "genérico"
                print(f"[{i}/{len(pendientes)}] {nombre:40} → {email} ({tipo})")
            else:
                campos["estado"] = "sin_email"
                sin_email += 1
                tel = f" | tel: {telefonos[0]}" if telefonos else ""
                print(f"[{i}/{len(pendientes)}] {nombre:40} → sin email{tel}")

            actualizar_lead(lead["id"], **campos)

    print(f"\nCon email: {con_email} | Sin email: {sin_email} | Sin web: {sin_web_marcados} | Tel: {con_telefono}")
    print("Resumen:", stats())


if __name__ == "__main__":
    main()
