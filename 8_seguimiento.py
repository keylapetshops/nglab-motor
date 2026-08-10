"""NGLAB Motor — Paso 8: Secuencia automática de seguimiento por email.

Lógica de envío:
  Email 2 → leads en `email_1_enviado` con fecha_email_1 >= 3 días · no dados de baja
  Email 3 → leads en `email_2_enviado` con fecha_email_1 >= 7 días · no dados de baja

Secuencia completa (días desde email 1):
  Día 0  → Email 1 (7_enviar_lote.py)
  Día 3  → Email 2 (este script)
  Día 7  → Email 3 (este script)

Uso manual:
  python3 8_seguimiento.py
"""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    REMITENTE_NOMBRE, REMITENTE_EMAIL,
    SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID, BASE_URL,
)
from db import actualizar_lead, ahora

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


# ─────────────────────────────────────────────
# Consultas a Supabase con filtro de fecha
# ─────────────────────────────────────────────

def leads_para_email2() -> list[dict]:
    """Leads en email_1_enviado con fecha_email_1 hace 3+ días."""
    with httpx.Client(timeout=15) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads",
            headers=HEADERS,
            params={
                "org_id": f"eq.{ORG_ID}",
                "estado": "eq.email_1_enviado",
                "dado_de_baja": "eq.false",
                "fecha_email_1": f"lte.{_hace_dias(3)}",
                "select": "id,nombre_negocio,email,email_asunto,pain_points,token_baja,sector,ciudad",
            },
        )
    r.raise_for_status()
    return r.json()


def leads_para_email3() -> list[dict]:
    """Leads en email_2_enviado con fecha_email_1 hace 7+ días."""
    with httpx.Client(timeout=15) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads",
            headers=HEADERS,
            params={
                "org_id": f"eq.{ORG_ID}",
                "estado": "eq.email_2_enviado",
                "dado_de_baja": "eq.false",
                "fecha_email_1": f"lte.{_hace_dias(7)}",
                "select": "id,nombre_negocio,email,email_asunto,pain_points,token_baja,sector,ciudad",
            },
        )
    r.raise_for_status()
    return r.json()


def _hace_dias(n: int) -> str:
    """Devuelve timestamp ISO de hace N días (para filtro lte)."""
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


# ─────────────────────────────────────────────
# Plantillas de email
# ─────────────────────────────────────────────

def _primer_pain_point(lead: dict) -> str:
    """Extrae el primer pain point del lead."""
    pp = lead.get("pain_points") or []
    if isinstance(pp, list) and pp:
        # Acortar si es muy largo
        return pp[0][:120]
    return "la presencia digital del negocio"


def generar_email2(lead: dict) -> tuple[str, str, str]:
    """Genera asunto, texto plano y HTML para el email de seguimiento 2."""
    nombre = lead.get("nombre_negocio", "")
    pain   = _primer_pain_point(lead)
    token  = lead.get("token_baja", "")
    url_baja = f"{BASE_URL}/baja/{token}" if token else "#"
    url_pixel = f"{BASE_URL}/px/{token}.gif" if token else ""

    asunto = f"Re: {lead.get('email_asunto', nombre)} — ¿pudiste verlo?"

    texto = f"""Hola,

Te escribía hace unos días sobre {pain}.

¿Has tenido oportunidad de echarle un vistazo? Sé que el día a día no deja mucho tiempo, pero me gustaría saber si tiene sentido hablar.

Si te viene bien una llamada rápida de 15 minutos esta semana, dímelo y lo organizamos.

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    pixel = f'<img src="{url_pixel}" width="1" height="1" style="display:none" />' if url_pixel else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:system-ui,sans-serif;color:#1a1a1a;max-width:560px;margin:0 auto;padding:24px 16px;line-height:1.6">

  <p>Hola,</p>

  <p>Te escribía hace unos días sobre <strong>{pain}</strong>.</p>

  <p>¿Has tenido oportunidad de echarle un vistazo? Sé que el día a día no deja mucho tiempo,
  pero me gustaría saber si tiene sentido hablar.</p>

  <p>Si te viene bien una <strong>llamada rápida de 15 minutos</strong> esta semana,
  dímelo y lo organizamos sin compromiso.</p>

  <p style="margin-top:32px">Un saludo,<br>
  <strong>Jesica Márquez</strong><br>
  N&amp;G LAB Digital<br>
  <a href="https://nglabdigital.com" style="color:#C8FF00">nglabdigital.com</a></p>

  <hr style="border:none;border-top:1px solid #eee;margin:32px 0">
  <p style="font-size:12px;color:#999">
    Si no deseas recibir más emails de nuestra parte,
    <a href="{url_baja}" style="color:#999">pulsa aquí para darte de baja</a>.
  </p>
  {pixel}
</body>
</html>"""

    return asunto, texto, html


def generar_email3(lead: dict) -> tuple[str, str, str]:
    """Genera asunto, texto plano y HTML para el email de seguimiento 3 (último)."""
    nombre = lead.get("nombre_negocio", "")
    pain   = _primer_pain_point(lead)
    token  = lead.get("token_baja", "")
    url_baja  = f"{BASE_URL}/baja/{token}" if token else "#"
    url_pixel = f"{BASE_URL}/px/{token}.gif" if token else ""

    asunto = f"Último mensaje · {nombre}"

    texto = f"""Hola,

Este es mi último mensaje, no quiero ser pesada.

Te contacté porque detectamos que {pain}, y creemos que podemos ayudaros a mejorar eso.

Si en algún momento os interesa, aquí estaremos. Solo tienes que responder a este email.

Mucho ánimo con el negocio,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    pixel = f'<img src="{url_pixel}" width="1" height="1" style="display:none" />' if url_pixel else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:system-ui,sans-serif;color:#1a1a1a;max-width:560px;margin:0 auto;padding:24px 16px;line-height:1.6">

  <p>Hola,</p>

  <p>Este es mi último mensaje, no quiero ser pesada.</p>

  <p>Te contacté porque detectamos que <strong>{pain}</strong>,
  y creemos que podemos ayudaros a mejorar eso.</p>

  <p>Si en algún momento os interesa, aquí estaremos.
  Solo tienes que responder a este email.</p>

  <p style="margin-top:32px">Mucho ánimo con el negocio,<br>
  <strong>Jesica Márquez</strong><br>
  N&amp;G LAB Digital<br>
  <a href="https://nglabdigital.com" style="color:#C8FF00">nglabdigital.com</a></p>

  <hr style="border:none;border-top:1px solid #eee;margin:32px 0">
  <p style="font-size:12px;color:#999">
    Si no deseas recibir más emails de nuestra parte,
    <a href="{url_baja}" style="color:#999">pulsa aquí para darte de baja</a>.
  </p>
  {pixel}
</body>
</html>"""

    return asunto, texto, html


# ─────────────────────────────────────────────
# Envío SMTP
# ─────────────────────────────────────────────

def _enviar_smtp(email_to: str, asunto: str, texto: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
    msg["To"]      = email_to
    msg["Reply-To"] = REMITENTE_EMAIL
    msg.attach(MIMEText(texto, "plain", "utf-8"))
    msg.attach(MIMEText(html,  "html",  "utf-8"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def enviar_seguimiento() -> dict:
    """Ejecuta la secuencia de emails 2 y 3. Devuelve resumen."""
    import time
    enviados2 = 0
    enviados3 = 0
    errores   = 0

    # ── Email 2 (día 3) ──────────────────────────────────────────────────
    pendientes2 = leads_para_email2()
    print(f"[SEGUIMIENTO] Email 2: {len(pendientes2)} leads pendientes")

    for lead in pendientes2:
        nombre   = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        if not email_to:
            continue
        try:
            asunto, texto, html = generar_email2(lead)
            _enviar_smtp(email_to, asunto, texto, html)
            actualizar_lead(
                lead["id"],
                estado="email_2_enviado",
                fecha_email_2=ahora(),
                secuencia_email=2,
            )
            enviados2 += 1
            print(f"  ✓ Email 2 → {nombre[:40]} ({email_to})")
        except Exception as e:
            errores += 1
            print(f"  ✗ Error email 2 → {nombre[:40]}: {e}")
        time.sleep(3)

    # ── Email 3 (día 7) ──────────────────────────────────────────────────
    pendientes3 = leads_para_email3()
    print(f"[SEGUIMIENTO] Email 3: {len(pendientes3)} leads pendientes")

    for lead in pendientes3:
        nombre   = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        if not email_to:
            continue
        try:
            asunto, texto, html = generar_email3(lead)
            _enviar_smtp(email_to, asunto, texto, html)
            actualizar_lead(
                lead["id"],
                estado="email_3_enviado",
                fecha_email_3=ahora(),
                secuencia_email=3,
            )
            enviados3 += 1
            print(f"  ✓ Email 3 → {nombre[:40]} ({email_to})")
        except Exception as e:
            errores += 1
            print(f"  ✗ Error email 3 → {nombre[:40]}: {e}")
        time.sleep(3)

    resumen = {
        "email_2_enviados": enviados2,
        "email_3_enviados": enviados3,
        "errores": errores,
    }
    print(f"[SEGUIMIENTO] Resumen: {resumen}")
    return resumen


if __name__ == "__main__":
    enviar_seguimiento()
