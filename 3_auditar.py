"""NGLAB Motor — Paso 3: Auditoría web + PageSpeed (diferenciador N&G LAB).

Para cada lead con email analiza:
  - Estado de la web (activa, HTTPS, móvil, SEO básico)
  - Velocidad de carga real (PageSpeed API)
  - Presencia en redes sociales
  - Citas/reservas online
  - WhatsApp en la web

Para leads SIN web analiza:
  - Datos de Google Business (calificación, reseñas)
  - Ausencia de presencia digital como pain point principal

Traduce los resultados a pain points concretos del nicho.

Uso:
    python3 3_auditar.py
    python3 3_auditar.py dental    # solo un nicho
"""
import json
import sys
import time

import httpx
from bs4 import BeautifulSoup

from config import NICHOS, PAGESPEED_API_KEY, nicho_config
from db import leads_por_estado, actualizar_lead, stats, ahora

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

CITAS_ONLINE = [
    "thefork", "eltenedor", "covermanager", "booksy", "treatwell",
    "timify", "calendly", "resurva", "reservio", "bewe.", "flowww",
    "citaonline", "cita-online", "cita previa online", "reserva online",
    "reservar online", "pedir cita online", "book online",
]


def auditar_web(url: str) -> dict:
    """Analiza la web del lead y devuelve un dict con los resultados."""
    a: dict = {"web_activa": False}
    try:
        inicio = time.monotonic()
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(
                url if url.startswith("http") else "https://" + url,
                headers={"User-Agent": UA}
            )
        a["tiempo_carga_s"] = round(time.monotonic() - inicio, 2)

        if r.status_code != 200:
            a["error"] = f"HTTP {r.status_code}"
            return a

        a["web_activa"] = True
        a["https"] = str(r.url).startswith("https://")

        html = r.text.lower()
        soup = BeautifulSoup(r.text, "html.parser")

        a["movil_optimizada"] = bool(
            soup.find("meta", attrs={"name": "viewport"})
        )
        a["tiene_titulo_seo"] = bool(
            soup.title and soup.title.string
            and len(soup.title.string.strip()) > 5
        )
        a["tiene_meta_descripcion"] = bool(
            soup.find("meta", attrs={"name": "description"})
        )
        a["tiene_instagram"] = "instagram.com" in html
        a["tiene_facebook"] = "facebook.com" in html
        a["tiene_whatsapp"] = "wa.me" in html or "api.whatsapp.com" in html
        a["tiene_citas_online"] = any(k in html for k in CITAS_ONLINE)

    except httpx.HTTPError as e:
        a["error"] = type(e).__name__
    return a


def obtener_pagespeed(url: str) -> dict:
    """Llama a PageSpeed API y devuelve las métricas clave."""
    if not PAGESPEED_API_KEY:
        return {}
    try:
        api_url = (
            f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
            f"?url={url}&strategy=mobile&key={PAGESPEED_API_KEY}&category=performance&category=accessibility&category=best-practices&category=seo"
        )
        with httpx.Client(timeout=60) as c:
            r = c.get(api_url)
        if r.status_code != 200:
            return {"error": f"PageSpeed HTTP {r.status_code}"}

        data = r.json()
        cats = data.get("lighthouseResult", {}).get("categories", {})
        audits = data.get("lighthouseResult", {}).get("audits", {})

        return {
            "puntuacion_mobile": round(
                (cats.get("performance", {}).get("score", 0) or 0) * 100
            ),
            "accesibilidad": round(
                (cats.get("accessibility", {}).get("score", 0) or 0) * 100
            ),
            "buenas_practicas": round(
                (cats.get("best-practices", {}).get("score", 0) or 0) * 100
            ),
            "seo": round(
                (cats.get("seo", {}).get("score", 0) or 0) * 100
            ),
            "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", ""),
            "fid": audits.get("total-blocking-time", {}).get("displayValue", ""),
            "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
            "fcp": audits.get("first-contentful-paint", {}).get("displayValue", ""),
        }
    except Exception as e:
        return {"error": str(e)[:100]}


def detectar_pain_points(lead: dict, auditoria: dict,
                         pagespeed: dict) -> list[str]:
    """Traduce la auditoría en dolores de negocio concretos del nicho."""
    nicho = lead.get("sector") or "otro"
    cfg = NICHOS.get(nicho, NICHOS["otro"])
    dolores: list[str] = []
    a = auditoria

    if not a.get("web_activa"):
        dolores.append(
            "Su web no responde o da error: pierden clientes que "
            "les buscan online cada día"
        )
        dolores.append(f"Problema del sector: {cfg['dolor']}")
        return dolores[:4]

    # PageSpeed — puntuación baja
    ps = pagespeed.get("puntuacion_mobile", 0)
    if ps and ps < 50:
        dolores.append(
            f"Vuestra web tiene una puntuación de velocidad de {ps}/100 en móvil: "
            "Google penaliza las webs lentas y los usuarios las abandonan antes de ver el negocio"
        )
    elif ps and ps < 80:
        dolores.append(
            f"La velocidad en móvil es mejorable ({ps}/100): "
            "el 80% de los clientes buscan desde el móvil y cada segundo de espera "
            "son clientes que se van"
        )

    # HTTPS
    if not a.get("https"):
        dolores.append(
            "La web no usa HTTPS: el navegador la marca como 'No segura' "
            "y Google la penaliza en el posicionamiento"
        )

    # móvil
    if not a.get("movil_optimizada"):
        dolores.append(
            "La web no está optimizada para móvil: el 80% de sus clientes "
            "buscan desde el teléfono y probablemente la están viendo mal"
        )

    # Citas online
    if not a.get("tiene_citas_online"):
        dolores.append(
            f"Sin sistema de reservas/citas online: {cfg['dolor']}"
        )

    # WhatsApp
    if not a.get("tiene_whatsapp"):
        dolores.append(
            "Sin botón de WhatsApp en la web: los clientes prefieren "
            "escribir antes que llamar, y sin ese canal los pierden"
        )

    # SEO básico
    if not a.get("tiene_titulo_seo") or not a.get("tiene_meta_descripcion"):
        dolores.append(
            "SEO básico sin trabajar: pierden visibilidad en búsquedas "
            "locales frente a competidores que sí lo tienen configurado"
        )

    return dolores[:4]


def detectar_pain_points_sin_web(lead: dict) -> list[str]:
    """Genera pain points para leads SIN web usando datos de Google Business."""
    nicho = lead.get("sector") or "otro"
    cfg = NICHOS.get(nicho, NICHOS["otro"])
    dolores: list[str] = []

    calificacion = lead.get("calificacion_google")
    resenas = lead.get("resenas_google") or 0

    # Pain point principal: no tienen web
    dolores.append(
        f"Sin página web propia: cuando alguien busca en Google, "
        f"solo ven el perfil de Maps — pierden clientes frente a "
        f"competidores que sí tienen web y aparecen primero"
    )

    # Pocas reseñas en Google
    if resenas < 10:
        dolores.append(
            f"Solo {resenas} reseña{'s' if resenas != 1 else ''} en Google: "
            f"los clientes comparan antes de llamar y eligen negocios "
            f"con más valoraciones"
        )
    elif resenas < 50:
        dolores.append(
            f"Con {resenas} reseñas en Google tienen base, pero sus "
            f"competidores con más valoraciones se llevan la mayoría de clics"
        )

    # Calificación baja
    if calificacion is not None and calificacion < 4.0:
        dolores.append(
            f"Calificación de {calificacion}/5 en Google: "
            f"la mayoría de clientes descarta negocios por debajo de 4 estrellas "
            f"sin ni siquiera llamar"
        )
    elif calificacion is not None and calificacion < 4.5:
        dolores.append(
            f"Con {calificacion}/5 en Google están bien, pero los negocios "
            f"con 4.5+ se llevan el doble de clics en los resultados locales"
        )

    # Sin presencia digital = sin reservas fuera de horario
    dolores.append(
        f"Sin web no pueden recibir {cfg.get('dolor', 'solicitudes de clientes')} "
        f"fuera del horario de atención — cada noche pierden oportunidades"
    )

    return dolores[:4]


def main(nicho: str | None = None):
    if nicho is None:
        nicho = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if nicho:
        nicho_config(nicho)

    # ── FLUJO 1: Leads CON web ──────────────────────────────────────────────
    pendientes_con_web = leads_por_estado("pendiente_revision", con_web=True, nicho=nicho)
    print(f"Leads CON web pendientes de auditoría: {len(pendientes_con_web)}")

    for i, lead in enumerate(pendientes_con_web, 1):
        web = lead.get("web", "")
        if not web:
            continue

        # Auditoría básica
        a = auditar_web(web)

        # PageSpeed (el diferenciador de N&G LAB)
        ps = obtener_pagespeed(web) if a.get("web_activa") else {}

        # Pain points
        dolores = detectar_pain_points(lead, a, ps)

        # Guardar en Supabase
        actualizar_lead(
            lead["id"],
            auditoria=json.dumps({**a, "pagespeed": ps}, ensure_ascii=False),
            pain_points=dolores,
            estado="auditado",
            fecha_analisis=ahora(),
        )

        ps_score = ps.get("puntuacion_mobile", "?")
        print(
            f"[{i}/{len(pendientes_con_web)}] {lead['nombre_negocio'][:38]:38} "
            f"PS:{ps_score:>3} -> {len(dolores)} pain points"
        )
        time.sleep(0.5)

    # ── FLUJO 2: Leads SIN web ──────────────────────────────────────────────
    pendientes_sin_web = leads_por_estado("pendiente_revision", con_web=False, nicho=nicho)
    print(f"\nLeads SIN web pendientes de auditoría: {len(pendientes_sin_web)}")

    for i, lead in enumerate(pendientes_sin_web, 1):
        # Pain points basados en Google Business
        dolores = detectar_pain_points_sin_web(lead)

        # Auditoría mínima para leads sin web
        a = {"web_activa": False, "sin_web": True}

        # Guardar en Supabase
        actualizar_lead(
            lead["id"],
            auditoria=json.dumps(a, ensure_ascii=False),
            pain_points=dolores,
            estado="auditado",
            fecha_analisis=ahora(),
        )

        print(
            f"[{i}/{len(pendientes_sin_web)}] {lead['nombre_negocio'][:38]:38} "
            f"Google:{lead.get('calificacion_google', '?')}★ "
            f"{lead.get('resenas_google', 0)} reseñas -> {len(dolores)} pain points"
        )
        time.sleep(0.1)

    print("\nResumen:", stats())


if __name__ == "__main__":
    main()
