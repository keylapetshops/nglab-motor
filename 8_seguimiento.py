"""NGLAB Motor — Paso 8: Secuencia automática de seguimiento por email.

Día 0 → Email 1 (7_enviar_lote.py)
Día 3 → Email 2 (este script) — personalizado si abrió el informe
Día 7 → Email 3 (este script) — último mensaje, activado
"""
from __future__ import annotations

import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    REMITENTE_NOMBRE, REMITENTE_EMAIL,
    SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID, BASE_URL,
)
from db import actualizar_lead, ahora

MOTOR_URL = "https://nglab-motor-production.up.railway.app"
WHATSAPP_NUM = "34673038773"

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def _hace_dias(n: int) -> str:
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def leads_para_email2() -> list[dict]:
    with httpx.Client(timeout=15) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads",
            headers=HEADERS,
            params={
                "org_id": f"eq.{ORG_ID}",
                "estado": "eq.email_1_enviado",
                "dado_de_baja": "eq.false",
                "fecha_email_1": f"lte.{_hace_dias(3)}",
                "select": "id,nombre_negocio,email,email_asunto,pain_points,email_cuerpo,token_baja,sector,ciudad,veces_abierto_informe,url_informe",
            },
        )
        r.raise_for_status()
        return r.json()


def leads_para_email3() -> list[dict]:
    with httpx.Client(timeout=15) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/crm_leads",
            headers=HEADERS,
            params={
                "org_id": f"eq.{ORG_ID}",
                "estado": "eq.email_2_enviado",
                "dado_de_baja": "eq.false",
                "fecha_email_2": f"lte.{_hace_dias(7)}",
                "select": "id,nombre_negocio,email,email_asunto,pain_points,email_cuerpo,token_baja,sector,ciudad,veces_abierto_informe,url_informe",
            },
        )
        r.raise_for_status()
        return r.json()


def _primer_pain_point(lead: dict) -> str:
    pp = lead.get("pain_points") or []
    if isinstance(pp, list) and pp:
        return pp[0][:120]
    cuerpo = lead.get("email_cuerpo") or ""
    for linea in cuerpo.split("\n"):
        linea = linea.strip()
        if linea.startswith("→"):
            punto = linea.lstrip("→").strip()
            if punto:
                return punto[:160]
    return "vuestra presencia digital"


def _url_informe(lead: dict) -> str:
    lead_id = lead.get("id", "")
    return lead.get("url_informe") or f"{MOTOR_URL}/informe/{lead_id}"


# ─────────────────────────────────────────────
# EMAIL 2 — Día 3
# ─────────────────────────────────────────────

def generar_email2(lead: dict) -> tuple[str, str, str]:
    nombre = lead.get("nombre_negocio", "")
    sector = lead.get("sector", "otro")
    pain = _primer_pain_point(lead)
    token = lead.get("token_baja", "")
    url_baja = f"{BASE_URL}/baja/{token}" if token else "#"
    veces_informe = lead.get("veces_abierto_informe", 0) or 0
    url_inf = _url_informe(lead)
    wa_url = f"https://wa.me/{WHATSAPP_NUM}?text=Hola+Jesica,+quiero+saber+más+sobre+{nombre.replace(' ', '+')}"

    # ── ESTÉTICA: foco en no-shows ────────────────────────────────────────
    if sector == "estetica":
        asunto = f"{nombre}: ¿cuántas citas se cancelaron esta semana sin avisar?"

        if veces_informe > 0:
            intro_texto = f"Te escribí hace unos días sobre la presencia digital de {nombre} — veo que pudiste echarle un vistazo al análisis."
            intro_html = f"Te escribí hace unos días sobre la presencia digital de <strong>{nombre}</strong> — veo que pudiste echarle un vistazo al análisis."
        else:
            intro_texto = f"Te escribí hace unos días sobre la presencia digital de {nombre}. Por si no llegaste a verlo, aquí tienes el informe: {url_inf}"
            intro_html = f"Te escribí hace unos días sobre la presencia digital de <strong>{nombre}</strong>. Por si no llegaste a verlo, <a href='{url_inf}' style='color:#C8FF00'>aquí tienes el informe</a>."

        texto = f"""Hola,

{intro_texto}

Hoy quiero hablarte de algo que nos dicen casi todos los centros de estética con los que trabajamos: las cancelaciones de última hora.

Una cabina vacía por un no-show son entre 60€ y 180€ perdidos. Multiplicado por 3 o 4 a la semana — estamos hablando de más de 500€ al mes que simplemente desaparecen de la agenda.

El problema no es que los clientes sean malos — es que sin un sistema que gestione la reserva correctamente, el no-show es inevitable:

→ Sin confirmación automática 24h antes, la cita se olvida
→ Sin pago o señal en la reserva, cancelar no cuesta nada
→ Sin lista de espera activa, esa hora queda vacía aunque haya clientes que querían ese hueco

Nosotros implementamos ese sistema en menos de una semana.

Si quieres verlo en detalle, escríbeme:
{wa_url}

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

        html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f5f0eb;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 16px">
<table width="560" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:12px;overflow:hidden;max-width:560px;box-shadow:0 2px 12px rgba(0,0,0,0.08)">

<tr>
<td style="background:#1a1a2e;padding:22px 28px">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td><span style="color:#C8FF00;font-size:18px;font-weight:800;letter-spacing:2px">N&amp;G LAB</span>
<span style="color:#555;font-size:11px;margin-left:10px;letter-spacing:1px">DIGITAL AGENCY</span></td>
<td align="right"><span style="background:#e8c4b8;color:#6b2d1f;font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px">PARA CENTROS DE ESTÉTICA</span></td>
</tr>
<tr><td colspan="2" style="padding-top:14px">
<p style="margin:0;color:#fff;font-size:16px;font-weight:700;line-height:1.4">{nombre},<br>
<span style="color:#aaa;font-weight:400;font-size:14px">¿cuántas citas perdiste esta semana por no-shows?</span></p>
</td></tr>
</table>
</td>
</tr>

<tr>
<td style="background:#fff8f5;padding:16px 28px;border-bottom:2px solid #e8c4b8">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="80" style="text-align:center">
<div style="font-size:28px;font-weight:800;color:#c0392b;line-height:1">500€</div>
<div style="font-size:10px;color:#888;margin-top:2px">pérdida/mes</div>
</td>
<td width="1" style="padding:0 14px"><div style="width:1px;height:40px;background:#e8c4b8"></div></td>
<td style="padding-left:4px">
<p style="margin:0;font-size:12px;color:#6b2d1f;line-height:1.6">Una cabina vacía por un no-show son entre <strong>60€ y 180€ perdidos</strong>. Multiplicado por 3-4 a la semana.</p>
</td>
</tr></table>
</td>
</tr>

<tr><td style="padding:24px 28px">
<p style="margin:0 0 6px;color:#999;font-size:11px;font-weight:600;letter-spacing:1px">HOLA,</p>
<p style="margin:0 0 20px;color:#1a1a1a;font-size:14px;line-height:1.7">{intro_html}<br><br>
Hoy quiero hablarte de algo que nos dicen casi todos los centros de estética: <strong>las cancelaciones de última hora</strong>.</p>

<p style="margin:0 0 12px;font-size:13px;font-weight:700;color:#1a1a1a">El problema no son los clientes — es el sistema:</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px"><tr>
<td width="36" valign="top" style="padding-top:2px"><div style="width:28px;height:28px;background:#fff0ed;border-radius:50%;text-align:center;line-height:28px;font-size:16px">📅</div></td>
<td style="padding-left:10px;background:#fafafa;border-radius:8px;padding:10px 14px;border:1px solid #f0e8e4">
<p style="margin:0 0 3px;font-size:12px;font-weight:700;color:#1a1a1a">Sin confirmación automática</p>
<p style="margin:0;font-size:12px;color:#666;line-height:1.5">Sin recordatorio 24h antes, la cita se olvida y nadie avisa</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:10px"><tr>
<td width="36" valign="top" style="padding-top:2px"><div style="width:28px;height:28px;background:#fff0ed;border-radius:50%;text-align:center;line-height:28px;font-size:16px">💳</div></td>
<td style="padding-left:10px;background:#fafafa;border-radius:8px;padding:10px 14px;border:1px solid #f0e8e4">
<p style="margin:0 0 3px;font-size:12px;font-weight:700;color:#1a1a1a">Sin señal en la reserva</p>
<p style="margin:0;font-size:12px;color:#666;line-height:1.5">Cancelar no cuesta nada — la señal online hace que se lo piensen dos veces</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td width="36" valign="top" style="padding-top:2px"><div style="width:28px;height:28px;background:#fff0ed;border-radius:50%;text-align:center;line-height:28px;font-size:16px">⏳</div></td>
<td style="padding-left:10px;background:#fafafa;border-radius:8px;padding:10px 14px;border:1px solid #f0e8e4">
<p style="margin:0 0 3px;font-size:12px;font-weight:700;color:#1a1a1a">Sin lista de espera activa</p>
<p style="margin:0;font-size:12px;color:#666;line-height:1.5">Esa hora vacía podría haberse rellenado sola</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td style="background:#f0fff4;border-radius:8px;padding:16px 18px;border:1px solid #c6f6d5">
<p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#1a1a1a">✅ Lo implementamos en menos de una semana</p>
<p style="margin:0;font-size:12px;color:#276749;line-height:1.6">Confirmaciones automáticas por WhatsApp · Reserva con señal online · Lista de espera que rellena los huecos sola</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td style="background:#1a1a2e;border-radius:8px;padding:18px 20px;text-align:center">
<p style="margin:0 0 4px;color:#C8FF00;font-size:11px;font-weight:700;letter-spacing:1px">¿LO VEMOS JUNTAS?</p>
<p style="margin:0 0 14px;color:#888;font-size:11px">15 minutos · Sin compromiso · Elige cómo prefieres</p>
<a href="{wa_url}" style="background:#25D366;color:#fff;padding:11px 22px;border-radius:6px;font-weight:700;font-size:13px;text-decoration:none;display:inline-block;margin:0 6px 8px">💬 WhatsApp</a>
<a href="https://calendly.com/hola-nglabdigital/30min" style="background:#0069FF;color:#fff;padding:11px 22px;border-radius:6px;font-weight:700;font-size:13px;text-decoration:none;display:inline-block;margin:0 6px 8px">📅 Llamada</a>
</td></tr></table>

<table cellpadding="0" cellspacing="0" style="border-top:1px solid #f0f0f0;padding-top:16px;width:100%"><tr>
<td width="46" valign="middle"><div style="width:40px;height:40px;border-radius:50%;background:#C8FF00;text-align:center;line-height:40px;font-weight:700;font-size:13px;color:#14141A">JM</div></td>
<td style="padding-left:12px;padding-top:16px">
<p style="margin:0;font-size:13px;font-weight:700;color:#1a1a1a">Jesica Márquez</p>
<p style="margin:0;font-size:12px;color:#888">N&amp;G LAB Digital · <a href="https://nglabdigital.com" style="color:#C8FF00;text-decoration:none">nglabdigital.com</a></p>
</td></tr></table>
</td></tr>

<tr><td style="background:#f9f9f9;padding:12px 28px;border-top:1px solid #eee;text-align:center">
<p style="margin:0;font-size:11px;color:#aaa;line-height:1.6">Has recibido este email porque tu negocio aparece en Google Maps. N&amp;G LAB Digital ·
<a href="{url_baja}" style="color:#aaa;text-decoration:underline">No quiero recibir más emails</a></p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

        return asunto, texto, html

    # ── GENÉRICO (resto de sectores) ──────────────────────────────────────
    asunto_original = lead.get("email_asunto", nombre)
    asunto = f"Re: {asunto_original} — ¿pudiste verlo?"

    if veces_informe > 0:
        ref_informe_texto = f"Veo que pudiste ver el análisis que te preparé. ¿Tienes alguna pregunta?"
        ref_informe_html = f"Veo que pudiste ver el análisis que te preparé. ¿Tienes alguna pregunta?"
    else:
        ref_informe_texto = f"Por si no tuviste tiempo, aquí tienes el análisis: {url_inf}"
        ref_informe_html = f"Por si no tuviste tiempo, aquí tienes el análisis: <a href='{url_inf}' style='color:#C8FF00;font-weight:700'>Ver informe →</a>"

    texto = f"""Hola,

Te escribía hace unos días sobre {pain}.

{ref_informe_texto}

Si te viene bien una llamada rápida de 15 minutos esta semana, lo organizamos sin compromiso:
{wa_url}

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f0f0;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 16px">
<table width="560" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:10px;overflow:hidden;max-width:560px">

<tr><td style="background:#14141A;padding:22px 28px">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><span style="color:#C8FF00;font-size:18px;font-weight:800;letter-spacing:2px">N&amp;G LAB</span>
<span style="color:#555;font-size:11px;margin-left:10px;letter-spacing:1px">DIGITAL AGENCY</span></td>
<td align="right"><span style="background:#C8FF00;color:#14141A;font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px">SEGUIMIENTO</span></td>
</tr>
<tr><td colspan="2" style="padding-top:14px">
<p style="margin:0;color:#fff;font-size:16px;font-weight:700;line-height:1.4">{nombre},<br>
<span style="color:#aaa;font-weight:400;font-size:14px">¿pudiste ver nuestro análisis?</span></p>
</td></tr></table>
</td></tr>

<tr><td style="padding:24px 28px">
<p style="margin:0 0 6px;color:#999;font-size:11px;font-weight:600;letter-spacing:1px">HOLA,</p>
<p style="margin:0 0 18px;color:#1a1a1a;font-size:14px;line-height:1.7">Te escribía hace unos días sobre <strong>{pain}</strong>.</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td style="background:#fafafa;border-radius:8px;padding:16px 18px;border:1px solid #f0f0f0">
<p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#1a1a1a">¿Has tenido oportunidad de verlo?</p>
<p style="margin:0;font-size:12px;color:#555;line-height:1.6">{ref_informe_html}<br><br>
Si te viene bien una <strong>llamada rápida de 15 minutos</strong> esta semana, lo organizamos sin compromiso.</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td style="background:#14141A;border-radius:8px;padding:18px 20px;text-align:center">
<p style="margin:0 0 4px;color:#C8FF00;font-size:11px;font-weight:700;letter-spacing:1px">¿HABLAMOS 15 MINUTOS?</p>
<p style="margin:0 0 14px;color:#888;font-size:11px">Sin compromiso · Esta semana</p>
<a href="{wa_url}" style="background:#25D366;color:#fff;padding:11px 28px;border-radius:6px;font-weight:700;font-size:14px;text-decoration:none;display:inline-block">💬 Escribir a Jesica</a>
</td></tr></table>

<table cellpadding="0" cellspacing="0" style="border-top:1px solid #f0f0f0;padding-top:16px;width:100%"><tr>
<td width="46" valign="middle"><div style="width:40px;height:40px;border-radius:50%;background:#C8FF00;text-align:center;line-height:40px;font-weight:700;font-size:13px;color:#14141A">JM</div></td>
<td style="padding-left:12px;padding-top:16px">
<p style="margin:0;font-size:13px;font-weight:700;color:#1a1a1a">Jesica Márquez</p>
<p style="margin:0;font-size:12px;color:#888">N&amp;G LAB Digital · <a href="https://nglabdigital.com" style="color:#C8FF00;text-decoration:none">nglabdigital.com</a></p>
</td></tr></table>
</td></tr>

<tr><td style="background:#f9f9f9;padding:12px 28px;border-top:1px solid #eee;text-align:center">
<p style="margin:0;font-size:11px;color:#aaa;line-height:1.6">Has recibido este email porque tu negocio aparece en Google Maps. N&amp;G LAB Digital ·
<a href="{url_baja}" style="color:#aaa;text-decoration:underline">No quiero recibir más emails</a></p>
</td></tr>

</table></td></tr></table>
</body></html>"""

    return asunto, texto, html


# ─────────────────────────────────────────────
# EMAIL 3 — Día 7 — ACTIVADO
# ─────────────────────────────────────────────

def generar_email3(lead: dict) -> tuple[str, str, str]:
    nombre = lead.get("nombre_negocio", "")
    pain = _primer_pain_point(lead)
    token = lead.get("token_baja", "")
    url_baja = f"{BASE_URL}/baja/{token}" if token else "#"
    url_inf = _url_informe(lead)
    wa_url = f"https://wa.me/{WHATSAPP_NUM}?text=Hola+Jesica,+quiero+información+sobre+{nombre.replace(' ', '+')}"

    asunto = f"Último mensaje · {nombre}"

    texto = f"""Hola,

Este es mi último mensaje, no quiero ser pesada.

Te contacté porque detectamos que {pain}, y creemos que podemos ayudaros a mejorar eso.

Si quieres ver el análisis completo que preparamos para {nombre}:
{url_inf}

Y si en algún momento os interesa hablar, aquí estaremos:
{wa_url}

Mucho ánimo con el negocio,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f0f0;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:24px 16px">
<table width="560" cellpadding="0" cellspacing="0"
       style="background:#fff;border-radius:10px;overflow:hidden;max-width:560px">

<tr><td style="background:#14141A;padding:22px 28px">
<table width="100%" cellpadding="0" cellspacing="0"><tr>
<td><span style="color:#C8FF00;font-size:18px;font-weight:800;letter-spacing:2px">N&amp;G LAB</span>
<span style="color:#555;font-size:11px;margin-left:10px;letter-spacing:1px">DIGITAL AGENCY</span></td>
<td align="right"><span style="background:#555;color:#fff;font-size:10px;font-weight:700;padding:4px 10px;border-radius:20px">ÚLTIMO MENSAJE</span></td>
</tr>
<tr><td colspan="2" style="padding-top:14px">
<p style="margin:0;color:#fff;font-size:16px;font-weight:700;line-height:1.4">{nombre},<br>
<span style="color:#aaa;font-weight:400;font-size:14px">este es mi último mensaje</span></p>
</td></tr></table>
</td></tr>

<tr><td style="padding:24px 28px">
<p style="margin:0 0 6px;color:#999;font-size:11px;font-weight:600;letter-spacing:1px">HOLA,</p>
<p style="margin:0 0 18px;color:#1a1a1a;font-size:14px;line-height:1.7">Este es mi último mensaje, no quiero ser pesada.</p>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px"><tr>
<td style="background:#fafafa;border-radius:8px;padding:16px 18px;border:1px solid #f0f0f0">
<p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#1a1a1a">Lo que detectamos en vuestro caso</p>
<p style="margin:0;font-size:12px;color:#555;line-height:1.6">{pain}. Creemos que podemos ayudaros a mejorar eso.</p>
</td></tr></table>

<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:22px"><tr>
<td style="background:#14141A;border-radius:8px;padding:18px 20px;text-align:center">
<p style="margin:0 0 4px;color:#C8FF00;font-size:11px;font-weight:700;letter-spacing:1px">VUESTRO ANÁLISIS SIGUE DISPONIBLE</p>
<p style="margin:0 0 14px;color:#888;font-size:12px">Por si queréis revisarlo cuando tengáis un momento</p>
<a href="{url_inf}" style="background:#C8FF00;color:#14141A;padding:11px 28px;border-radius:6px;font-weight:800;font-size:14px;text-decoration:none;display:inline-block;margin-bottom:10px">Ver análisis →</a>
<br>
<a href="{wa_url}" style="color:#25D366;font-size:12px;font-weight:600;text-decoration:none">💬 O escríbenos por WhatsApp</a>
</td></tr></table>

<table cellpadding="0" cellspacing="0" style="border-top:1px solid #f0f0f0;padding-top:16px;width:100%"><tr>
<td width="46" valign="middle"><div style="width:40px;height:40px;border-radius:50%;background:#C8FF00;text-align:center;line-height:40px;font-weight:700;font-size:13px;color:#14141A">JM</div></td>
<td style="padding-left:12px;padding-top:16px">
<p style="margin:0;font-size:13px;font-weight:700;color:#1a1a1a">Jesica Márquez</p>
<p style="margin:0;font-size:12px;color:#888">N&amp;G LAB Digital · <a href="https://nglabdigital.com" style="color:#C8FF00;text-decoration:none">nglabdigital.com</a></p>
<p style="margin:4px 0 0;font-size:12px;color:#888">Mucho ánimo con el negocio 💪</p>
</td></tr></table>
</td></tr>

<tr><td style="background:#f9f9f9;padding:12px 28px;border-top:1px solid #eee;text-align:center">
<p style="margin:0;font-size:11px;color:#aaa;line-height:1.6">Has recibido este email porque tu negocio aparece en Google Maps. N&amp;G LAB Digital ·
<a href="{url_baja}" style="color:#aaa;text-decoration:underline">No quiero recibir más emails</a></p>
</td></tr>

</table></td></tr></table>
</body></html>"""

    return asunto, texto, html


# ─────────────────────────────────────────────
# Envío SMTP
# ─────────────────────────────────────────────

def _enviar_smtp(email_to: str, asunto: str, texto: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = f"{REMITENTE_NOMBRE} <{REMITENTE_EMAIL}>"
    msg["To"] = email_to
    msg["Reply-To"] = REMITENTE_EMAIL
    msg.attach(MIMEText(texto, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def enviar_seguimiento() -> dict:
    enviados2 = 0
    enviados3 = 0
    errores = 0

    # ── Email 2 (día 3) ──────────────────────────────────────────────────
    pendientes2 = leads_para_email2()
    print(f"[SEGUIMIENTO] Email 2: {len(pendientes2)} leads pendientes")

    for lead in pendientes2:
        nombre = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        if not email_to:
            continue
        try:
            asunto, texto, html = generar_email2(lead)
            _enviar_smtp(email_to, asunto, texto, html)
            actualizar_lead(lead["id"], estado="email_2_enviado", fecha_email_2=ahora(), secuencia_email=2)
            enviados2 += 1
            print(f"   ✓ Email 2 → {nombre[:40]} ({email_to})")
        except Exception as e:
            errores += 1
            print(f"   ✗ Error email 2 → {nombre[:40]}: {e}")
        time.sleep(3)

    # ── Email 3 (día 7) — ACTIVADO ────────────────────────────────────────
    pendientes3 = leads_para_email3()
    print(f"[SEGUIMIENTO] Email 3: {len(pendientes3)} leads pendientes")

    for lead in pendientes3:
        nombre = lead.get("nombre_negocio", "")
        email_to = lead.get("email", "")
        if not email_to:
            continue
        try:
            asunto, texto, html = generar_email3(lead)
            _enviar_smtp(email_to, asunto, texto, html)
            actualizar_lead(lead["id"], estado="email_3_enviado", fecha_email_3=ahora(), secuencia_email=3)
            enviados3 += 1
            print(f"   ✓ Email 3 → {nombre[:40]} ({email_to})")
        except Exception as e:
            errores += 1
            print(f"   ✗ Error email 3 → {nombre[:40]}: {e}")
        time.sleep(3)

    resumen = {"email_2_enviados": enviados2, "email_3_enviados": enviados3, "errores": errores}
    print(f"[SEGUIMIENTO] Resumen: {resumen}")
    return resumen


if __name__ == "__main__":
    enviar_seguimiento()
