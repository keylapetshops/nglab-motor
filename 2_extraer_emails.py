from __future__ import annotations
"""NGLAB Motor — Paso 2: Extraer emails de las webs de los leads.

MEJORAS v2:
  - Más rutas candidatas (footer, sobre-nosotros, quienes-somos, team, etc.)
  - Filtro avanzado de emails de empleados (prioriza genéricos siempre)
  - Lista negra ampliada de dominios temporales/desechables
  - Extracción de teléfonos como fallback si no hay email
  - Detección de patrones sospechosos (emails autogenerados, bots)
  - Decodificación Cloudflare mejorada
  - Cache de URLs visitadas para no repetir peticiones
  - Timeout inteligente por ruta

Leads sin web → estado 'sin_web' (cola llamada)
Leads con web sin email → estado 'sin_email' (cola llamada, guardamos teléfono si encontramos)
Leads con email → estado 'pendiente_revision'
"""
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import PREFIJOS_GENERICOS, DOMINIOS_BASURA, EXTENSIONES_FALSAS
from db import leads_por_estado, actualizar_lead, stats

# ── Rutas candidatas ampliadas ────────────────────────────────────────────────
RUTAS_CANDIDATAS = [
    "",
    "aviso-legal", "avisolegal", "aviso_legal", "legal", "aviso",
    "politica-de-privacidad", "politica-privacidad", "privacidad",
    "privacy", "privacy-policy", "politica", "rgpd", "lopd",
    "contacto", "contact", "contactanos", "contacta", "contacte",
    "contact-us", "contacto.html", "contacto.php",
    "sobre-nosotros", "sobre-nosotros.html", "quienes-somos",
    "quien-somos", "about", "about-us", "equipo", "team",
    "nosotros", "empresa",
    "footer", "pie-de-pagina", "informacion", "info",
]

REGEX_EMAIL = re.compile(
    r"\b[a-zA-Z0-9][a-zA-Z0-9._%+\-]{0,62}@"
    r"[a-zA-Z0-9][a-zA-Z0-9.\-]{0,61}[a-zA-Z0-9]"
    r"\.[a-zA-Z]{2,}\b"
)

REGEX_TELEFONO = re.compile(
    r"(?<!\d)"
    r"(?:\+34[\s\-]?)?"
    r"(?:6\d{2}|7[1-9]\d|8\d{2}|9\d{2})"
    r"[\s\-]?\d{3}[\s\-]?\d{3}"
    r"(?!\d)"
)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

DOMINIOS_TEMPORALES = {
    "mailinator.com", "tempmail.com", "guerrillamail.com",
    "10minutemail.com", "throwaway.email", "yopmail.com",
    "sharklasers.com", "guerrillamail.info", "guerrillamail.biz",
    "guerrillamail.de", "guerrillamail.net", "guerrillamail.org",
    "spam4.me", "trashmail.com", "trashmail.me", "trashmail.net",
    "dispostable.com", "mailnull.com", "spamgourmet.com",
    "maildrop.cc", "discard.email", "fakeinbox.com",
    "tempr.email", "tempinbox.com", "spamfree24.org",
    "mailexpire.com", "objectmail.com",
    "gmail.co", "gmail.con", "gmial.com", "gmai.com",
    "hotmail.co", "hotmail.con", "homail.com",
    "yahoo.co", "yaho.com", "yahooo.com",
    "outlook.co", "outlok.com",
}

PATRONES_SOSPECHOSOS = [
    re.compile(r"noreply", re.I),
    re.compile(r"no-reply", re.I),
    re.compile(r"donotreply", re.I),
    re.compile(r"mailer-daemon", re.I),
    re.compile(r"postmaster@", re.I),
    re.compile(r"wordpress@", re.I),
    re.compile(r"woocommerce@", re.I),
    re.compile(r"@example\.", re.I),
    re.compile(r"@test\.", re.I),
    re.compile(r"@domain\.", re.I),
    re.compile(r"\d{6,}@", re.I),
]


def decodificar_cfemail(cf: str) -> str:
    try:
        clave = int(cf[:2], 16)
        return "".join(
            chr(int(cf[i:i + 2], 16) ^ clave)
            for i in range(2, len(cf), 2)
        )
    except (ValueError, IndexError):
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
    if re.match(r"^[a-z]{2,}[._][a-z]{1,3}$", local):
        return True
    return False


def extraer_de_html(html: str) -> set[str]:
    encontrados: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.select('a[href^="mailto:"]'):
        email = a["href"].removeprefix("mailto:").split("?")[0].strip()
        if email and es_email_valido(email):
            encontrados.add(email.lower())

    for tag in soup.select("[data-cfemail]"):
        email = decodificar_cfemail(tag["data-cfemail"])
        if email and es_email_valido(email):
            encontrados.add(email.lower())

    texto = soup.get_text(" ")
    for e in REGEX_EMAIL.findall(texto):
        e = e.strip(".,;:\"'()[]").lower()
        if es_email_valido(e):
            encontrados.add(e)

    for e in REGEX_EMAIL.findall(html):
        e = e.strip(".,;:\"'()[]").lower()
        if es_email_valido(e):
            encontrados.add(e)

    return encontrados


def extraer_telefonos(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    telefonos = []

    for a in soup.select('a[href^="tel:"]'):
        tel = a["href"].replace("tel:", "").strip()
        tel = re.sub(r"[^\d+]", "", tel)
        if len(tel) >= 9:
            telefonos.append(tel)

    if not telefonos:
        texto = soup.get_text(" ")
        for t in REGEX_TELEFONO.findall(texto):
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
        local   = e.split("@")[0].lower()
        dominio = e.split("@")[1].lower()
        es_gen  = any(local == p or local.startswith(p) for p in PREFIJOS_GENERICOS)
        es_prop = bool(dominio_web and dominio_web in dominio)
        es_empl = es_email_empleado(e)
        return (
            not (es_gen and es_prop),
            not es_gen,
            not es_prop,
            es_empl,
            len(e),
        )

    return sorted(emails, key=puntuar)[0]


def procesar_lead(lead: dict, cliente: httpx.Client) -> tuple[str | None, str | None, list[str]]:
    base = lead.get("web", "")
    if not base or not base.strip():
        return None, None, []

    base = base.strip()

    # FIX: descartar URLs inválidas que causan crash (solo "/", "//", rutas relativas)
    if base in ("/", "//", "#") or base.startswith("javascript:"):
        return None, None, []

    # Añadir esquema si falta
    if not base.startswith(("http://", "https://")):
        base = "https://" + base

    parsed = urlparse(base)

    # Verificar que tiene dominio real con punto
    if not parsed.netloc or "." not in parsed.netloc:
        return None, None, []

    dominio_web = parsed.netloc.removeprefix("www.")

    todos_emails:    set[str]  = set()
    todos_telefonos: list[str] = []
    mejor_fuente:    str | None = None
    rutas_visitadas: set[str]  = set()

    for ruta in RUTAS_CANDIDATAS:
        url = urljoin(base if base.endswith("/") else base + "/", ruta)
        if url in rutas_visitadas:
            continue
        rutas_visitadas.add(url)

        try:
            r = cliente.get(url, headers={"User-Agent": UA}, timeout=10)
            if r.status_code != 200:
                continue
            if "text/html" not in r.headers.get("content-type", ""):
                continue

            emails_pagina = extraer_de_html(r.text)
            todos_emails.update(emails_pagina)

            if not todos_telefonos:
                todos_telefonos = extraer_telefonos(r.text)

            # Si ya tenemos email genérico del dominio propio, paramos
            mejor = elegir_mejor(todos_emails, dominio_web)
            if mejor and not es_email_empleado(mejor):
                local = mejor.split("@")[0].lower()
                if any(local == p or local.startswith(p) for p in PREFIJOS_GENERICOS):
                    if dominio_web and dominio_web in mejor.split("@")[1]:
                        mejor_fuente = str(r.url)
                        break

        except (httpx.HTTPError, httpx.TimeoutException):
            continue

        time.sleep(0.2)

    mejor_email = elegir_mejor(todos_emails, dominio_web)
    if mejor_email and not mejor_fuente:
        mejor_fuente = base

    return mejor_email, mejor_fuente, todos_telefonos


def main():
    # ── Leads SIN web → cola llamada ─────────────────────────────────────────
    sin_web = leads_por_estado("nuevo", con_web=False)
    sin_web_marcados = 0
    for lead in sin_web:
        if not lead.get("web"):
            actualizar_lead(lead["id"], estado="sin_web")
            sin_web_marcados += 1
    if sin_web_marcados:
        print(f"Leads sin web → cola llamada: {sin_web_marcados}")

    # ── Leads CON web → extraer email ────────────────────────────────────────
    pendientes = leads_por_estado("nuevo", con_web=True)
    print(f"Leads con web pendientes: {len(pendientes)}")

    con_email    = 0
    sin_email    = 0
    con_telefono = 0

    with httpx.Client(timeout=15, follow_redirects=True) as cliente:
        for i, lead in enumerate(pendientes, 1):
            nombre = lead.get("nombre_negocio", lead.get("nombre", ""))[:40]
            email, fuente, telefonos = procesar_lead(lead, cliente)

            campos: dict = {}

            if telefonos and not lead.get("telefono"):
                campos["telefono"] = telefonos[0]
                con_telefono += 1

            if email:
                campos.update({
                    "email":  email,
                    "notas":  f"Email extraído de: {fuente}",
                    "estado": "pendiente_revision",
                })
                con_email += 1
                tipo = "empleado" if es_email_empleado(email) else "genérico"
                print(f"[{i}/{len(pendientes)}] {nombre:40} → {email} ({tipo})")
            else:
                campos["estado"] = "sin_email"
                sin_email += 1
                tel_info = f" | tel: {telefonos[0]}" if telefonos else ""
                print(f"[{i}/{len(pendientes)}] {nombre:40} → sin email{tel_info}")

            actualizar_lead(lead["id"], **campos)

    print(f"\nResultados:")
    print(f"  Con email:    {con_email}")
    print(f"  Sin email:    {sin_email}")
    print(f"  Sin web:      {sin_web_marcados}")
    print(f"  Tel extraído: {con_telefono}")
    print("Resumen:", stats())


if __name__ == "__main__":
    main()
