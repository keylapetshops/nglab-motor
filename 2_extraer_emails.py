from __future__ import annotations
"""NGLAB Motor — Paso 2: Extraer emails de las webs de los leads.

Estrategia (orden de prioridad):
  1. Aviso legal / política de privacidad (obligatorio LSSI Art. 10)
  2. Página de contacto
  3. Portada (mailto:, texto plano, ofuscación Cloudflare)

Solo se guardan buzones corporativos/genéricos cuando hay varios candidatos
(info@, reservas@...) para minimizar tratamiento de datos de personas físicas.

Leads sin web → estado 'sin_web' (cola de llamada/WhatsApp, nunca email)
Leads con web sin email → estado 'sin_email' (cola de llamada/WhatsApp)
Leads con email → estado 'pendiente_revision' (cola de email)
"""
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from config import PREFIJOS_GENERICOS, DOMINIOS_BASURA, EXTENSIONES_FALSAS
from db import leads_por_estado, actualizar_lead, stats

RUTAS_CANDIDATAS = [
    "",
    "aviso-legal", "avisolegal", "aviso_legal", "legal",
    "politica-de-privacidad", "politica-privacidad", "privacidad", "privacy",
    "contacto", "contact", "contactanos", "contacta",
]

REGEX_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def decodificar_cfemail(cf: str) -> str:
    """Decodifica emails ofuscados por Cloudflare (data-cfemail, XOR simple)."""
    try:
        clave = int(cf[:2], 16)
        return "".join(chr(int(cf[i:i + 2], 16) ^ clave)
                       for i in range(2, len(cf), 2))
    except (ValueError, IndexError):
        return ""


def es_email_valido(email: str) -> bool:
    e = email.lower()
    if e.endswith(EXTENSIONES_FALSAS):
        return False
    dominio = e.split("@")[-1]
    if any(basura in dominio for basura in DOMINIOS_BASURA):
        return False
    if len(e) > 80 or e.count("@") != 1:
        return False
    return True


def extraer_de_html(html: str) -> set[str]:
    encontrados: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    # 1) mailto:
    for a in soup.select('a[href^="mailto:"]'):
        email = a["href"].removeprefix("mailto:").split("?")[0].strip()
        if email:
            encontrados.add(email)

    # 2) Ofuscación Cloudflare
    for tag in soup.select("[data-cfemail]"):
        email = decodificar_cfemail(tag["data-cfemail"])
        if email:
            encontrados.add(email)

    # 3) Texto plano + HTML crudo
    encontrados.update(REGEX_EMAIL.findall(soup.get_text(" ")))
    encontrados.update(REGEX_EMAIL.findall(html))

    return {e.strip(".,;:").lower() for e in encontrados if es_email_valido(e)}


def elegir_mejor(emails: set[str], dominio_web: str) -> str | None:
    """Prioriza: prefijo genérico + dominio propio > genérico > dominio propio > resto."""
    if not emails:
        return None

    def puntuar(e: str) -> tuple:
        prefijo = e.split("@")[0]
        dominio = e.split("@")[-1]
        es_generico = any(prefijo == p or prefijo.startswith(p)
                          for p in PREFIJOS_GENERICOS)
        es_propio = bool(dominio_web and dominio_web in dominio)
        return (not (es_generico and es_propio), not es_generico,
                not es_propio, len(e))

    return sorted(emails, key=puntuar)[0]


def procesar_lead(lead: dict, cliente: httpx.Client) -> tuple[str | None, str | None]:
    base = lead.get("web", "")
    parsed = urlparse(base)
    if not parsed.scheme:
        base = "https://" + base
        parsed = urlparse(base)
    dominio_web = parsed.netloc.removeprefix("www.")

    for ruta in RUTAS_CANDIDATAS:
        url = urljoin(base if base.endswith("/") else base + "/", ruta)
        try:
            r = cliente.get(url, headers={"User-Agent": UA})
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
                continue
            emails = extraer_de_html(r.text)
            mejor = elegir_mejor(emails, dominio_web)
            if mejor:
                return mejor, str(r.url)
        except httpx.HTTPError:
            continue
        time.sleep(0.3)
    return None, None


def main():
    # ── FIX: Leads SIN web → estado 'sin_web' (cola llamada), NO descartado ──
    # Antes se descartaban perdiendo leads con teléfono válido para llamar.
    sin_web = leads_por_estado("nuevo", con_web=False)
    sin_web_marcados = 0
    for lead in sin_web:
        if not lead.get("web"):
            actualizar_lead(lead["id"], estado="sin_web")
            sin_web_marcados += 1
    if sin_web_marcados:
        print(f"Leads sin web → cola de llamada: {sin_web_marcados}")

    # ── Leads CON web: extraer email ─────────────────────────────────────────
    pendientes = leads_por_estado("nuevo", con_web=True)
    print(f"Leads con web pendientes de extracción: {len(pendientes)}")

    con_email = 0
    sin_email = 0

    with httpx.Client(timeout=15, follow_redirects=True) as cliente:
        for i, lead in enumerate(pendientes, 1):
            email, fuente = procesar_lead(lead, cliente)
            nombre = lead.get("nombre_negocio", lead.get("nombre", ""))[:40]
            if email:
                actualizar_lead(lead["id"],
                                email=email,
                                notas=f"Email extraído de: {fuente}",
                                estado="pendiente_revision")
                con_email += 1
                print(f"[{i}/{len(pendientes)}] {nombre:40} -> {email}")
            else:
                # Sin email → cola de llamada, no descartado
                actualizar_lead(lead["id"], estado="sin_email")
                sin_email += 1
                print(f"[{i}/{len(pendientes)}] {nombre:40} -> sin email (cola llamada)")

    print(f"\nEmails encontrados: {con_email} · Sin email: {sin_email} · Sin web: {sin_web_marcados}")
    print("Resumen:", stats())


if __name__ == "__main__":
    main()
