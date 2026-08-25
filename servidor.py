from __future__ import annotations
"""NGLAB Motor — Servidor API (FastAPI) para Railway.

Endpoints:
  POST /api/prospectar        -> lanza el pipeline en segundo plano
  GET  /api/prospectar/estado -> estado del motor
  GET  /api/lote              -> leads listos para enviar (para n8n)
  POST /api/enviado/{id}      -> marca un lead como enviado
  GET  /api/stats             -> métricas del embudo
  GET  /baja/{token}          -> baja voluntaria LSSI (público)
  GET  /px/{token}.gif        -> pixel de tracking de apertura (público)
  GET  /salud                 -> healthcheck Railway (público)

Variables de entorno necesarias en Railway:
  MOTOR_API_KEY, GOOGLE_PLACES_API_KEY, PAGESPEED_API_KEY,
  ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY,
  ORG_ID, BASE_URL, REMITENTE_NOMBRE, REMITENTE_EMAIL,
  EMPRESA_LEGAL, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, LOTE_DIARIO

Arranque Railway: uvicorn servidor:app --host 0.0.0.0 --port $PORT
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from config import (LOTE_DIARIO, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                    REMITENTE_NOMBRE, REMITENTE_EMAIL, EMPRESA_LEGAL, BASE_URL)
from db import lote_para_envio, actualizar_lead, excluir_email, stats, ahora, email_excluido
from motor import ejecutar_pipeline, estado_motor, siguientes_combos

MOTOR_API_KEY = os.getenv("MOTOR_API_KEY", "")

app = FastAPI(title="NGLAB Motor", docs_url=None, redoc_url=None)

# Pixel GIF transparente 1x1 para tracking de apertura de email
_PIXEL_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00"
    b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
    b"\x00\x00\x02\x02D\x01\x00;"
)


def verificar(x_api_key: str | None) -> None:
    """Autenticación simple por cabecera X-API-Key."""
    if not MOTOR_API_KEY:
        print("[AVISO] MOTOR_API_KEY no definida: API sin protección")
        return
    if x_api_key != MOTOR_API_KEY:
        raise HTTPException(401, "X-API-Key inválida o ausente")


# --------------------------------------------------------------------------
# Endpoints públicos
# --------------------------------------------------------------------------

@app.get("/salud")
def salud():
    return {"ok": True, "servicio": "NGLAB Motor"}



# User-Agents de bots/escáneres que NO cuentan como apertura real
_BOT_AGENTS = [
    "googlebot", "bingbot", "slurp", "duckduckbot", "baidu", "yandex",
    "barracuda", "proofpoint", "mimecast", "symantec", "sophos", "forcepoint",
    "ironport", "messagelabs", "postini", "cloudmark", "spamassassin",
    "python-requests", "python-httpx", "curl", "wget", "libwww", "java/",
    "apache-httpclient", "microsoft office", "outlook", "preview", "prefetch",
    "validator", "checker", "scanner", "bot", "spider", "crawl",
]

@app.get("/px/{token}.gif")
def pixel(token: str, request: Request):
    """Marca la apertura del email. Endpoint público."""
    # Filtrar bots y escáneres automáticos
    ua = (request.headers.get("user-agent") or "").lower()
    if not ua or any(b in ua for b in _BOT_AGENTS):
        return Response(
            content=_PIXEL_GIF,
            media_type="image/gif",
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    import httpx
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(timeout=5) as c:
            r = c.get(
                f"{SUPABASE_URL}/rest/v1/crm_leads"
                f"?token_baja=eq.{token}&org_id=eq.{ORG_ID}"
                f"&select=id,fecha_apertura_email,veces_abierto_email",
                headers=headers,
            )
            if r.status_code == 200 and r.json():
                lead = r.json()[0]
                veces = (lead.get("veces_abierto_email") or 0) + 1
                campos = {
                    "veces_abierto_email": veces,
                    "updated_at": ahora(),
                }
                if not lead.get("fecha_apertura_email"):
                    campos["fecha_apertura_email"] = ahora()
                c.patch(
                    f"{SUPABASE_URL}/rest/v1/crm_leads"
                    f"?token_baja=eq.{token}&org_id=eq.{ORG_ID}",
                    headers=headers,
                    json=campos,
                )
    except Exception:
        pass

    return Response(
        content=_PIXEL_GIF,
        media_type="image/gif",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/baja/{token}", response_class=HTMLResponse)
def baja(token: str):
    """Procesa la baja voluntaria LSSI. Endpoint público."""
    import httpx
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=10) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads"
            f"?token_baja=eq.{token}&org_id=eq.{ORG_ID}"
            f"&select=email,nombre_negocio",
            headers=headers,
        )
    if r.status_code != 200 or not r.json():
        raise HTTPException(404, "Enlace de baja no válido")

    lead = r.json()[0]
    email = lead.get("email")
    if not email:
        raise HTTPException(404, "Enlace de baja no válido")

    excluir_email(email, motivo="baja_voluntaria")

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Baja confirmada · N&G LAB</title>
<style>
  body {{ background:#141414; color:#e8e8e8; font-family:system-ui,sans-serif;
         display:grid; place-items:center; min-height:100vh; margin:0; }}
  .card {{ max-width:420px; padding:2.5rem; text-align:center; }}
  h1 {{ color:#C8FF00; font-size:1.4rem; }}
  p {{ opacity:.75; line-height:1.5; }}
</style></head>
<body><div class="card">
  <h1>Baja confirmada</h1>
  <p>El buzón <strong>{email}</strong> no volverá a recibir
  comunicaciones comerciales de N&amp;G LAB Digital.</p>
  <p>Gracias por tu tiempo.</p>
</div></body></html>"""


# --------------------------------------------------------------------------
# Endpoint público: informe HTML por lead
# --------------------------------------------------------------------------

@app.get("/informe/{lead_id}", response_class=HTMLResponse)
def ver_informe(lead_id: str, preview: str = "0"):
    """Sirve el informe HTML de un lead. ?preview=1 para ver sin contar apertura."""
    import json as _json
    import importlib
    import httpx
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID

    _headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=10) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads"
            f"?id=eq.{lead_id}&org_id=eq.{ORG_ID}&select=*",
            headers=_headers,
        )
    if r.status_code != 200 or not r.json():
        raise HTTPException(404, "Informe no encontrado")

    lead = r.json()[0]

    # Tracking de apertura — solo si NO es preview
    if preview != "1":
        try:
            veces  = (lead.get("veces_abierto_informe") or 0) + 1
            campos = {
                "veces_abierto_informe": veces,
                "updated_at": ahora(),
            }
            if not lead.get("fecha_apertura_informe"):
                campos["fecha_apertura_informe"] = ahora()
            with httpx.Client(timeout=5) as c:
                c.patch(
                    f"{SUPABASE_URL}/rest/v1/crm_leads"
                    f"?id=eq.{lead_id}&org_id=eq.{ORG_ID}",
                    headers=_headers,
                    json=campos,
                )
        except Exception:
            pass

    # Extraer puntuacion_mobile del JSON de auditoría
    auditoria_raw = lead.get("auditoria") or "{}"
    try:
        auditoria = _json.loads(auditoria_raw) if isinstance(auditoria_raw, str) else auditoria_raw
    except Exception:
        auditoria = {}
    ps_data = auditoria.get("pagespeed") or {}
    lead["pagespeed_mobile"] = ps_data.get("puntuacion_mobile", 0) or 0

    mod  = importlib.import_module("6_generar_informe")
    html = mod.generar_html(lead)
    return HTMLResponse(content=html)


# --------------------------------------------------------------------------
# Endpoints protegidos
# --------------------------------------------------------------------------

@app.post("/api/prospectar")
def api_prospectar(
    tareas: BackgroundTasks,
    municipios: int = 3,
    x_api_key: str | None = Header(default=None),
):
    """Lanza el pipeline automático en segundo plano."""
    verificar(x_api_key)
    if estado_motor["ocupado"]:
        raise HTTPException(409, "Ya hay una prospección en curso")
    municipios = max(1, min(municipios, 10))
    proximos = siguientes_combos(municipios)
    if not proximos:
        return {"ok": True, "mensaje": "Todo prospectado. Añade nichos en config.py."}
    tareas.add_task(ejecutar_pipeline, municipios)
    return {
        "ok": True,
        "lanzado": True,
        "nicho": proximos[0][0],
        "municipios": [m for _, m, _ in proximos],
        "nota": "Ejecutando en segundo plano.",
    }


@app.get("/api/prospectar/estado")
def api_prospectar_estado(x_api_key: str | None = Header(default=None)):
    verificar(x_api_key)
    return estado_motor


@app.get("/api/stats")
def api_stats(x_api_key: str | None = Header(default=None)):
    verificar(x_api_key)
    return stats()


@app.get("/api/lote")
def api_lote(
    limite: int = LOTE_DIARIO,
    x_api_key: str | None = Header(default=None),
):
    """Devuelve los leads listos para enviar email (para n8n)."""
    verificar(x_api_key)
    limite = max(1, min(limite, 100))
    leads = lote_para_envio(limite)
    return [
        {
            "id": l["id"],
            "nombre_negocio": l["nombre_negocio"],
            "sector": l.get("sector"),
            "ciudad": l.get("ciudad"),
            "email": l["email"],
            "email_asunto": l.get("email_asunto"),
            "email_cuerpo": l.get("email_cuerpo"),
            "email_html": l.get("email_html"),
            "token_baja": l.get("token_baja"),
        }
        for l in leads
    ]


@app.post("/api/enviado/{lead_id}")
def api_enviado(
    lead_id: str,
    x_api_key: str | None = Header(default=None),
):
    """n8n llama a este endpoint después de enviar el email."""
    verificar(x_api_key)
    ok = actualizar_lead(
        lead_id,
        estado="contactado",
        fecha_email=ahora(),
    )
    if not ok:
        raise HTTPException(404, "Lead no encontrado")
    return {"ok": True, "id": lead_id}


@app.post("/api/auditar")
def api_auditar(
    tareas: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
):
    """Lanza solo el paso 3 (auditoría + PageSpeed) sobre leads pendiente_revision."""
    verificar(x_api_key)
    def _run():
        import importlib
        importlib.import_module("3_auditar").main()
    tareas.add_task(_run)
    return {"ok": True, "mensaje": "Auditoría lanzada en segundo plano"}


@app.post("/api/generar")
def api_generar(
    tareas: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
):
    """Lanza solo el paso 4 (generar emails con plantilla) sobre leads auditados."""
    verificar(x_api_key)
    def _run():
        import importlib
        importlib.import_module("4_generar_emails").main()
    tareas.add_task(_run)
    return {"ok": True, "mensaje": "Generación de emails lanzada en segundo plano"}


@app.post("/api/enviar/lote")
def api_enviar_lote(x_api_key: str | None = Header(default=None)):
    """Dispara el envío del lote diario de forma manual."""
    verificar(x_api_key)
    try:
        import importlib
        mod = importlib.import_module("7_enviar_lote")
        enviados = mod.enviar_lote()
        return {"ok": True, "enviados": enviados}
    except Exception as e:
        raise HTTPException(500, f"Error en envío: {e}")


@app.post("/api/lead/{lead_id}/enviar")
def api_enviar_directo(
    lead_id: str,
    x_api_key: str | None = Header(default=None),
):
    """Envía el email a un lead concreto desde el panel (acción inmediata)."""
    verificar(x_api_key)
    if not SMTP_PASS:
        raise HTTPException(400, "Falta configurar SMTP_PASS")

    import httpx
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    with httpx.Client(timeout=10) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads?id=eq.{lead_id}&org_id=eq.{ORG_ID}",
            headers=headers,
        )
    if r.status_code != 200 or not r.json():
        raise HTTPException(404, "Lead no encontrado")

    lead = r.json()[0]
    if not lead.get("email"):
        raise HTTPException(400, "Este lead no tiene email")
    if lead.get("estado") == "descartado":
        raise HTTPException(409, "Lead dado de baja")

    asunto = lead.get("email_asunto")
    html   = lead.get("email_html")
    texto  = lead.get("email_cuerpo")

    if not asunto or not html:
        raise HTTPException(400, "El email aún no está generado. Ejecuta el pipeline primero.")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"] = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
        msg["To"] = lead["email"]
        msg["Reply-To"] = REMITENTE_EMAIL
        if texto:
            msg.attach(MIMEText(texto, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        raise HTTPException(502, f"Error enviando: {type(e).__name__}: {e}")

    actualizar_lead(lead_id, estado="contactado", fecha_email=ahora())
    return {"ok": True, "enviado_a": lead["email"]}


# --------------------------------------------------------------------------
# Scheduler automático - ejecuta pipeline a las 8:00 y envío a las 9:00 CEST
# --------------------------------------------------------------------------
import threading
from datetime import datetime, timezone, timedelta

ZONA_ESPANA = timezone(timedelta(hours=2))


def _scheduler_loop():
    """Hilo que revisa cada 60s si es hora de lanzar tareas programadas."""
    import time as _time
    # FIX: dos variables separadas — antes era una sola y el 08:00 bloqueaba el 09:00
    ultima_fecha_pipeline = None
    ultima_fecha_envio    = None

    while True:
        try:
            ahora_es  = datetime.now(ZONA_ESPANA)
            fecha_hoy = ahora_es.strftime("%Y-%m-%d")

            # 08:00 — pipeline de prospección
            if (ahora_es.hour == 8 and ahora_es.minute < 2
                    and fecha_hoy != ultima_fecha_pipeline):
                if not estado_motor["ocupado"]:
                    print(f"[SCHEDULER] {fecha_hoy} 08:00 – Lanzando pipeline automatico...")
                    try:
                        ejecutar_pipeline(3)
                    except Exception as e:
                        print(f"[SCHEDULER] Error pipeline: {e}")
                ultima_fecha_pipeline = fecha_hoy

            # 09:00 — envío de lote diario + secuencia de seguimiento
            if (ahora_es.hour == 9 and ahora_es.minute < 2
                    and fecha_hoy != ultima_fecha_envio):
                if not estado_motor["ocupado"]:
                    print(f"[SCHEDULER] {fecha_hoy} 09:00 – Enviando lote diario...")
                    try:
                        import importlib
                        mod = importlib.import_module("7_enviar_lote")
                        mod.enviar_lote()
                    except Exception as e:
                        print(f"[SCHEDULER] Error envio lote: {e}")
                    # Secuencia emails 2 y 3
                    try:
                        mod2 = importlib.import_module("8_seguimiento")
                        mod2.enviar_seguimiento()
                    except Exception as e:
                        print(f"[SCHEDULER] Error seguimiento: {e}")
                ultima_fecha_envio = fecha_hoy

        except Exception as e:
            print(f"[SCHEDULER] Error en loop: {e}")
        _time.sleep(60)


@app.on_event("startup")
def iniciar_scheduler():
    t = threading.Thread(target=_scheduler_loop, daemon=True)
    t.start()
    print("[SCHEDULER] Activo – pipeline 08:00 · emails 09:00 CEST")
