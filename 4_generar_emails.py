from __future__ import annotations
"""NGLAB Motor — Paso 4: Generar Email 1 por plantilla sin PageSpeed.

Email 1 — Día 0:
- Solo usa datos disponibles: Google Business (rating, reseñas), web activa o no,
  WhatsApp en web, citas online, pain points detectados en auditoría básica
- NO menciona velocidad web ni PageSpeed (eso va en Email 2)
- CTA principal: WhatsApp directo
- Sin botón de informe (el informe va en Email 2)

Cero coste de API. Sin dependencia de Anthropic.
"""
import sys
import time
from config import NICHOS
from db import leads_por_estado, actualizar_lead, cargar_json, stats

MOTOR_URL = "https://nglab-motor-production.up.railway.app"
WHATSAPP_NUM = "34673038773"


def _pain(dolores: list, idx: int, fallback: str = "") -> str:
    if not dolores or idx >= len(dolores):
        return fallback
    p = dolores[idx]
    if isinstance(p, dict):
        p = p.get("label") or p.get("descripcion") or p.get("code") or str(p)
    return str(p).strip()[:180]


def generar_asunto(lead: dict, cfg: dict) -> str:
    nombre = lead.get("nombre_negocio", "tu negocio")
    rating = lead.get("calificacion_google")
    resenas = lead.get("resenas_google", 0) or 0
    tiene_web = bool(lead.get("web", "").strip())

    if not tiene_web:
        return f"{nombre}: tus competidores te están ganando online"
    elif rating and float(rating) >= 4.5 and resenas > 50:
        return f"{nombre}: tienes buena reputación pero poca visibilidad digital"
    elif rating and float(rating) < 4.0:
        return f"{nombre}: hay algo que te está costando clientes"
    else:
        return f"He analizado la presencia digital de {nombre}"


def generar_email(lead: dict) -> dict | None:
    nicho      = lead.get("sector", "otro")
    cfg        = NICHOS.get(nicho, NICHOS["otro"])
    nombre     = lead.get("nombre_negocio", "")
    ciudad     = lead.get("ciudad", "")
    web        = lead.get("web", "")
    tiene_web  = bool(web and web.strip())
    rating     = lead.get("calificacion_google")
    resenas    = lead.get("resenas_google", 0) or 0
    token      = lead.get("token_baja", "")
    lead_id    = lead.get("id", "")
    sector_label = cfg.get("sector_label", "negocio local")
    necesita_citas = cfg.get("necesita_citas", False)

    # Pain points del lead
    dolores    = cargar_json(lead.get("pain_points")) or []
    dolor_cfg  = cfg.get("dolor", "")

    # Detectar datos de auditoría básica
    auditoria  = cargar_json(lead.get("auditoria")) or {}
    tiene_whatsapp  = auditoria.get("whatsapp", False)
    tiene_citas_web = auditoria.get("citas_online", False)
    tiene_https     = auditoria.get("https", True)
    movil_ok        = auditoria.get("movil_optimizada", True)

    # Construir pain points reales disponibles SIN PageSpeed
    puntos = []

    # Pain point 1: Reseñas y rating (dato concreto y personal)
    if rating and resenas:
        rating_f = float(rating)
        if rating_f >= 4.5 and resenas < 50:
            puntos.append(f"Tenéis un {rating}/5 con {resenas} reseñas — buena base, pero vuestros competidores con más de 100 reseñas aparecen antes en Google y se llevan más clics")
        elif rating_f >= 4.0:
            puntos.append(f"Con {resenas} reseñas y un {rating}/5 en Google tenéis credibilidad — pero sin una web bien posicionada esa reputación no se traduce en nuevos clientes")
        elif rating_f < 4.0:
            puntos.append(f"Vuestro {rating}/5 en Google con {resenas} reseñas está por debajo de la media del sector — cada valoración negativa sin respuesta aleja a potenciales clientes")
    elif tiene_web:
        puntos.append(dolor_cfg or f"Los clientes buscan {sector_label} en Google antes de llamar: sin buena presencia digital van a la competencia")

    # Pain point 2: WhatsApp / citas online
    if tiene_web:
        if necesita_citas and not tiene_citas_web:
            puntos.append(f"El 30% de las búsquedas de {sector_label} ocurren fuera del horario comercial — sin sistema de reserva online esos clientes van al competidor que sí permite reservar al instante")
        elif not tiene_whatsapp:
            puntos.append(f"Los clientes prefieren escribir por WhatsApp antes que llamar — sin botón de WhatsApp visible en vuestra web perdéis esos contactos directos")
        else:
            puntos.append(f"El 46% de las búsquedas en Google tienen intención local y el 88% de usuarios que busca un negocio local lo visita en 24 horas — cada día sin visibilidad digital es clientes que van a la competencia")
    else:
        puntos.append(f"Sin web propia solo existís en Google Maps — cuando alguien busca '{sector_label} en {ciudad}' vuestros competidores con web aparecen primero y se llevan esos clientes")

    # Pain point 3: Visibilidad IA — siempre aplica
    puntos.append(f"Cuando alguien le pregunta a ChatGPT o Google 'mejor {sector_label} en {ciudad}', {nombre} no aparece — y esto va a ser cada vez más determinante para captar nuevos clientes")

    # Pain point adicional de auditoría si hay
    if dolores:
        p_extra = _pain(dolores, 0, "")
        if p_extra and p_extra not in " ".join(puntos):
            puntos[1] = p_extra  # Reemplaza el punto 2 con dato real de auditoría

    asunto = generar_asunto(lead, cfg)
    url_baja   = f"{MOTOR_URL}/baja/{token}"
    url_pixel  = f"{MOTOR_URL}/px/{token}.gif"
    wa_texto   = f"Hola Jesica, he visto tu email sobre {nombre}".replace(" ", "+")
    wa_url     = f"https://wa.me/{WHATSAPP_NUM}?text={wa_texto}"

    # ── CUERPO TEXTO PLANO ────────────────────────────────────────────────────
    if tiene_web:
        intro_texto = f"He analizado la presencia digital de {nombre} y hay tres cosas que creo que os interesan saber:"
    else:
        intro_texto = f"He buscado {nombre} online y hay tres cosas que creo que os interesan saber:"

    cuerpo_texto = f"""Hola,

Soy Jesica, de N&G LAB Digital. Me dedico a ayudar a negocios como {nombre} a conseguir más clientes a través de internet.

{intro_texto}

→ {puntos[0]}

→ {puntos[1]}

→ {puntos[2]}

Si te viene bien hablar 15 minutos esta semana sobre cómo mejorar esto, escríbeme por WhatsApp y lo organizamos sin compromiso:
{wa_url}

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    # ── CUERPO HTML ───────────────────────────────────────────────────────────
    rating_badge = ""
    if rating and resenas:
        rating_f = float(rating)
        color_r = "#10B981" if rating_f >= 4.5 else "#F59E0B" if rating_f >= 4.0 else "#EF4444"
        rating_badge = f'<span style="background:{color_r};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700">{"★" * round(rating_f)} {rating}/5 · {resenas} reseñas</span>'

    if tiene_web:
        intro_html = f"He analizado la presencia digital de <strong>{nombre}</strong> {rating_badge} y hay tres cosas que creo que os interesan saber:"
    else:
        intro_html = f"He buscado <strong>{nombre}</strong> online {rating_badge} y hay tres cosas que creo que os interesan saber:"

    cuerpo_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:system-ui,-apple-system,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:24px 16px">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:8px;overflow:hidden;max-width:560px;box-shadow:0 2px 8px rgba(0,0,0,0.08)">

        <!-- Header -->
        <tr>
          <td style="background:#14141A;padding:20px 32px">
            <span style="color:#C8FF00;font-size:20px;font-weight:800;letter-spacing:2px">N&amp;G LAB</span>
            <span style="color:#555;font-size:12px;margin-left:12px;letter-spacing:1px">DIGITAL AGENCY</span>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px">
            <p style="margin:0 0 16px;color:#1a1a1a;font-size:15px">Hola,</p>

            <p style="margin:0 0 20px;color:#1a1a1a;font-size:14px;line-height:1.7">
              Soy <strong>Jesica</strong>, de N&amp;G LAB Digital. Me dedico a ayudar a negocios locales como <strong>{nombre}</strong> a conseguir más clientes a través de internet.
            </p>

            <p style="margin:0 0 20px;color:#1a1a1a;font-size:14px;line-height:1.7">{intro_html}</p>

            <!-- Pain points -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="margin:0 0 24px;border-radius:6px;overflow:hidden;border:1px solid #f0f0f0">
              <tr>
                <td style="padding:14px 18px;color:#333;font-size:13px;line-height:1.6;border-left:3px solid #C8FF00;background:#fafafa">
                  <strong style="color:#C8FF00">→</strong>&nbsp; {puntos[0]}
                </td>
              </tr>
              <tr>
                <td style="padding:14px 18px;color:#333;font-size:13px;line-height:1.6;border-left:3px solid #C8FF00;border-top:1px solid #f0f0f0;background:#fafafa">
                  <strong style="color:#C8FF00">→</strong>&nbsp; {puntos[1]}
                </td>
              </tr>
              <tr>
                <td style="padding:14px 18px;color:#333;font-size:13px;line-height:1.6;border-left:3px solid #C8FF00;border-top:1px solid #f0f0f0;background:#fafafa">
                  <strong style="color:#C8FF00">→</strong>&nbsp; {puntos[2]}
                </td>
              </tr>
            </table>

            <p style="margin:0 0 20px;color:#1a1a1a;font-size:14px;line-height:1.7">
              Si te viene bien hablar <strong>15 minutos esta semana</strong>,
              escríbeme por WhatsApp y lo organizamos sin compromiso:
            </p>

            <p style="text-align:center;margin:0 0 28px">
              <a href="{wa_url}"
                 style="background:#25D366;color:#fff;padding:12px 28px;border-radius:6px;
                        font-weight:700;font-size:14px;text-decoration:none;display:inline-block">
                💬 Escribir por WhatsApp
              </a>
            </p>

            <!-- Firma -->
            <table cellpadding="0" cellspacing="0" style="border-top:1px solid #f0f0f0;padding-top:20px;margin-top:4px">
              <tr>
                <td style="padding-top:16px;color:#1a1a1a;font-size:13px;line-height:1.8">
                  Un saludo,<br>
                  <strong style="font-size:14px">Jesica Márquez</strong><br>
                  <span style="color:#888">N&amp;G LAB Digital ·
                    <a href="https://nglabdigital.com" style="color:#C8FF00;text-decoration:none">nglabdigital.com</a>
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer LSSI -->
        <tr>
          <td style="background:#f9f9f9;padding:14px 32px;border-top:1px solid #eee;text-align:center">
            <p style="margin:0;font-size:11px;color:#aaa;line-height:1.6">
              Has recibido este email porque tu negocio aparece en Google Maps.<br>
              N&amp;G LAB Digital · nglabdigital.com<br>
              <a href="{url_baja}" style="color:#aaa;text-decoration:underline">
                No quiero recibir más emails
              </a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

  <!-- Pixel tracking apertura email -->
  <img src="{url_pixel}" width="1" height="1" style="display:none" alt="">
</body>
</html>"""

    return {
        "asunto": asunto,
        "cuerpo_texto": cuerpo_texto,
        "cuerpo_html": cuerpo_html,
    }


def main(nicho=None):
    # Procesar leads auditados (tienen PageSpeed) y pendiente_revision (sin PageSpeed)
    # Para Email 1 procesamos ambos — no necesitamos PageSpeed
    leads = []
    leads += leads_por_estado("auditado", nicho=nicho)
    leads += leads_por_estado("pendiente_revision", nicho=nicho)

    print(f"[EMAIL1] {len(leads)} leads para generar Email 1")

    ok = error = 0

    for lead in leads:
        lid    = lead.get("id")
        nombre = lead.get("nombre_negocio", "")[:50]
        n      = nicho or lead.get("sector", "otro")
        if n not in NICHOS:
            n = "otro"

        r = generar_email(lead)
        if r:
            actualizar_lead(
                lid,
                email_asunto=r["asunto"],
                email_cuerpo=r["cuerpo_texto"],
                email_html=r["cuerpo_html"],
                estado="listo_para_enviar",
            )
            ok += 1
            print(f"  OK  {nombre}")
        else:
            error += 1
            print(f"  ERR {nombre}")

        time.sleep(0.05)

    print(f"[EMAIL1] {ok} generados · {error} errores")
    print("Resumen:", stats())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
