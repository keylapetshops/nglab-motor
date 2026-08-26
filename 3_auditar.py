"""NGLAB Motor — Paso 3: Auditoría web + PageSpeed (diferenciador N&G LAB)."""
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

# Directorios médicos — no son webs propias del negocio
DIRECTORIOS = [
    "doctory.es", "doctoralia.es", "doctoralia.com", "topdoctors.es",
    "topdoctors.com", "tuotromedico.com", "mundodentista.com",
    "mundomed.com", "mimedico.com", "doctorin.es", "docdoc.es",
    "webconsultas.com", "saludonnet.com", "findoc.es",
    "paginasamarillas.es", "yelp.es", "yelp.com",
    "google.com/maps", "maps.google", "goo.gl",
    "facebook.com", "instagram.com", "twitter.com", "linkedin.com",
]

def es_directorio(url: str) -> bool:
    """Devuelve True si la URL pertenece a un directorio, no a una web propia."""
    if not url:
        return False
    url_lower = url.lower()
    return any(d in url_lower for d in DIRECTORIOS)


def _url_valida(url: str):
    if not url or not url.strip():
        return None
    url = url.strip()
    if url in ("/", "//", "#") or url.startswith("javascript:"):
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        return None
    return url


def auditar_web(url: str) -> dict:
    a: dict = {"web_activa": False}
    url_limpia = _url_valida(url)
    if not url_limpia:
        a["error"] = f"URL invalida: {url!r}"
        return a
    try:
        inicio = time.monotonic()
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(url_limpia, headers={"User-Agent": UA})
        a["tiempo_carga_s"] = round(time.monotonic() - inicio, 2)
        if r.status_code != 200:
            a["error"] = f"HTTP {r.status_code}"
            return a
        a["web_activa"] = True
        a["https"] = str(r.url).startswith("https://")
        html = r.text.lower()
        soup = BeautifulSoup(r.text, "html.parser")
        a["movil_optimizada"] = bool(soup.find("meta", attrs={"name": "viewport"}))
        a["tiene_titulo_seo"] = bool(soup.title and soup.title.string and len(soup.title.string.strip()) > 5)
        a["tiene_meta_descripcion"] = bool(soup.find("meta", attrs={"name": "description"}))
        a["tiene_instagram"] = "instagram.com" in html
        a["tiene_facebook"] = "facebook.com" in html
        a["tiene_whatsapp"] = "wa.me" in html or "api.whatsapp.com" in html
        a["tiene_citas_online"] = any(k in html for k in CITAS_ONLINE)
    except httpx.HTTPError as e:
        a["error"] = type(e).__name__
    return a


def obtener_pagespeed(url: str, reintentos: int = 2) -> dict:
    if not PAGESPEED_API_KEY:
        return {}
    url_limpia = _url_valida(url)
    if not url_limpia:
        return {"error": f"URL invalida: {url!r}"}
    url = url_limpia
    api_url = (
        f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        f"?url={url}&strategy=mobile&key={PAGESPEED_API_KEY}"
        f"&category=performance&category=accessibility&category=best-practices&category=seo"
    )
    for intento in range(1, reintentos + 2):
        try:
            with httpx.Client(timeout=90) as c:
                r = c.get(api_url)
            if r.status_code == 429:
                print(f"  [PageSpeed] Rate limit — esperando 30s...")
                time.sleep(30)
                continue
            if r.status_code >= 500:
                print(f"  [PageSpeed] Error {r.status_code} intento {intento}/{reintentos+1} — reintentando...")
                time.sleep(5)
                continue
            if r.status_code != 200:
                return {"error": f"PageSpeed HTTP {r.status_code}"}
            data = r.json()
            cats   = data.get("lighthouseResult", {}).get("categories", {})
            audits = data.get("lighthouseResult", {}).get("audits", {})
            resultado = {
                "puntuacion_mobile": round((cats.get("performance", {}).get("score", 0) or 0) * 100),
                "accesibilidad": round((cats.get("accessibility", {}).get("score", 0) or 0) * 100),
                "buenas_practicas": round((cats.get("best-practices", {}).get("score", 0) or 0) * 100),
                "seo": round((cats.get("seo", {}).get("score", 0) or 0) * 100),
                "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", ""),
                "fid": audits.get("total-blocking-time", {}).get("displayValue", ""),
                "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", ""),
                "fcp": audits.get("first-contentful-paint", {}).get("displayValue", ""),
            }
            scores = [resultado["puntuacion_mobile"], resultado["accesibilidad"],
                      resultado["buenas_practicas"], resultado["seo"]]
            if all(s == 0 for s in scores) and intento <= reintentos:
                print(f"  [PageSpeed] Scores a 0 — reintentando ({intento}/{reintentos+1})...")
                time.sleep(5)
                continue
            return resultado
        except httpx.TimeoutException:
            if intento <= reintentos:
                print(f"  [PageSpeed] Timeout intento {intento}/{reintentos+1} — reintentando...")
                time.sleep(5)
            else:
                return {"error": "timeout_tras_reintentos"}
        except Exception as e:
            return {"error": str(e)[:100]}
    return {"error": "max_reintentos_alcanzados"}


def detectar_pain_points(lead: dict, auditoria: dict, pagespeed: dict) -> list[str]:
    nicho = lead.get("sector") or "otro"
    cfg = NICHOS.get(nicho, NICHOS["otro"])
    dolores: list[str] = []
    a = auditoria
    if not a.get("web_activa"):
        dolores.append("Su web no responde o da error: pierden clientes que les buscan online cada día")
        dolores.append(f"Problema del sector: {cfg['dolor']}")
        return dolores[:4]
    ps = pagespeed.get("puntuacion_mobile", 0)
    if ps and ps < 50:
        dolores.append(f"Vuestra web tiene una puntuación de velocidad de {ps}/100 en móvil: Google penaliza las webs lentas y los usuarios las abandonan antes de ver el negocio")
    elif ps and ps < 80:
        dolores.append(f"La velocidad en móvil es mejorable ({ps}/100): el 80% de los clientes buscan desde el móvil y cada segundo de espera son clientes que se van")
    if not a.get("https"):
        dolores.append("La web no usa HTTPS: el navegador la marca como 'No segura' y Google la penaliza en el posicionamiento")
    if not a.get("movil_optimizada"):
        dolores.append("La web no está optimizada para móvil: el 80% de sus clientes buscan desde el teléfono y probablemente la están viendo mal")
    if not a.get("tiene_citas_online"):
        dolores.append(f"Sin sistema de reservas/citas online: {cfg['dolor']}")
    if not a.get("tiene_whatsapp"):
        dolores.append("Sin botón de WhatsApp en la web: los clientes prefieren escribir antes que llamar, y sin ese canal los pierden")
    if not a.get("tiene_titulo_seo") or not a.get("tiene_meta_descripcion"):
        dolores.append("SEO básico sin trabajar: pierden visibilidad en búsquedas locales frente a competidores que sí lo tienen configurado")
    return dolores[:4]


def detectar_pain_points_sin_web(lead: dict) -> list[str]:
    nicho = lead.get("sector") or "otro"
    cfg = NICHOS.get(nicho, NICHOS["otro"])
    dolores: list[str] = []
    calificacion = lead.get("calificacion_google")
    resenas = lead.get("resenas_google") or 0
    dolores.append(f"Sin página web propia: cuando alguien busca en Google, solo ven el perfil de Maps — pierden clientes frente a competidores que sí tienen web y aparecen primero")
    if resenas < 10:
        dolores.append(f"Solo {resenas} reseña{'s' if resenas != 1 else ''} en Google: los clientes comparan antes de llamar y eligen negocios con más valoraciones")
    elif resenas < 50:
        dolores.append(f"Con {resenas} reseñas en Google tienen base, pero sus competidores con más valoraciones se llevan la mayoría de clics")
    if calificacion is not None and calificacion < 4.0:
        dolores.append(f"Calificación de {calificacion}/5 en Google: la mayoría de clientes descarta negocios por debajo de 4 estrellas sin ni siquiera llamar")
    elif calificacion is not None and calificacion < 4.5:
        dolores.append(f"Con {calificacion}/5 en Google están bien, pero los negocios con 4.5+ se llevan el doble de clics en los resultados locales")
    dolores.append(f"Sin web no pueden recibir {cfg.get('dolor', 'solicitudes de clientes')} fuera del horario de atención — cada noche pierden oportunidades")
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

        # NUEVO: detectar directorios y tratar como sin web propia
        if es_directorio(web):
            print(f"[{i}/{len(pendientes_con_web)}] {lead['nombre_negocio'][:38]:38} → DIRECTORIO, tratando como sin web")
            dolores = detectar_pain_points_sin_web(lead)
            actualizar_lead(
                lead["id"],
                web=None,
                url_informe=None,
                auditoria=json.dumps({"web_activa": False, "sin_web": True, "motivo": "directorio"}, ensure_ascii=False),
                pain_points=dolores,
                estado="auditado",
                fecha_analisis=ahora(),
            )
            time.sleep(0.1)
            continue

        a = auditar_web(web)
        ps = obtener_pagespeed(web) if a.get("web_activa") else {}
        dolores = detectar_pain_points(lead, a, ps)
        actualizar_lead(
            lead["id"],
            auditoria=json.dumps({**a, "pagespeed": ps}, ensure_ascii=False),
            pain_points=dolores,
            estado="auditado",
            fecha_analisis=ahora(),
        )
        ps_score = ps.get("puntuacion_mobile", "?")
        print(f"[{i}/{len(pendientes_con_web)}] {lead['nombre_negocio'][:38]:38} PS:{ps_score:>3} -> {len(dolores)} pain points")
        time.sleep(0.5)

    # ── FLUJO 2: Leads SIN web ──────────────────────────────────────────────
    pendientes_sin_web = leads_por_estado("pendiente_revision", con_web=False, nicho=nicho)
    print(f"\nLeads SIN web pendientes de auditoría: {len(pendientes_sin_web)}")

    for i, lead in enumerate(pendientes_sin_web, 1):
        dolores = detectar_pain_points_sin_web(lead)
        a = {"web_activa": False, "sin_web": True}
        actualizar_lead(
            lead["id"],
            auditoria=json.dumps(a, ensure_ascii=False),
            pain_points=dolores,
            estado="auditado",
            fecha_analisis=ahora(),
        )
        print(f"[{i}/{len(pendientes_sin_web)}] {lead['nombre_negocio'][:38]:38} Google:{lead.get('calificacion_google', '?')}★ {lead.get('resenas_google', 0)} reseñas -> {len(dolores)} pain points")
        time.sleep(0.1)

    print("\nResumen:", stats())


if __name__ == "__main__":
    main()
