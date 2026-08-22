from __future__ import annotations
"""NGLAB Motor — Paso 4: Generar emails por plantilla (sin API de Claude).

Cada nicho tiene su propia plantilla personalizada.
Se usan los datos reales del lead: nombre, ciudad, pain points, PageSpeed, rating.

Sin coste de API. Sin dependencia externa.
"""
import sys
import time
from config import NICHOS, nicho_config
from db import leads_por_estado, actualizar_lead, cargar_json

MOTOR_URL = "https://nglab-motor-production.up.railway.app"


def _pain(dolores: list, idx: int, fallback: str = "") -> str:
    """Extrae un pain point por índice de forma segura."""
    if not dolores or idx >= len(dolores):
        return fallback
    p = dolores[idx]
    if isinstance(p, dict):
        p = p.get("label") or p.get("code") or str(p)
    return str(p)[:150]


def generar_asunto(lead: dict, cfg: dict) -> str:
    nombre  = lead.get("nombre_negocio", "tu negocio")
    ciudad  = lead.get("ciudad", "")
    sector  = cfg.get("sector_label", "negocio")
    ps      = int(lead.get("pagespeed_mobile", 0) or 0)

    if ps and ps < 50:
        return f"{nombre}: tu web pierde clientes cada día"
    elif ps and ps < 80:
        return f"{nombre}, hay margen de mejora en tu web"
    elif not lead.get("web"):
        return f"{nombre}: tus competidores te están ganando online"
    else:
        return f"He analizado la web de {nombre}"


def generar_email(lead: dict) -> dict | None:
    """Genera asunto + cuerpo texto + cuerpo HTML para un lead."""
    nicho   = lead.get("sector", "otro")
    cfg     = NICHOS.get(nicho, NICHOS["otro"])
    nombre  = lead.get("nombre_negocio", "")
    ciudad  = lead.get("ciudad", "")
    web     = lead.get("web", "")
    tiene_web = bool(web and web.strip())
    ps      = int(lead.get("pagespeed_mobile", 0) or 0)
    rating  = lead.get("calificacion_google", "")
    resenas = lead.get("resenas_google", 0) or 0
    token   = lead.get("token_baja", "")
    lead_id = lead.get("id", "")

    dolores = cargar_json(lead.get("pain_points")) or []
    dolor1  = _pain(dolores, 0, cfg["dolor"])
    dolor2  = _pain(dolores, 1, "la web no está optimizada para móvil")
    dolor3  = _pain(dolores, 2, "sin visibilidad en buscadores locales")

    url_informe = f"{MOTOR_URL}/informe/{lead_id}"
    url_baja    = f"{MOTOR_URL}/baja/{token}"
    url_pixel   = f"{MOTOR_URL}/px/{token}.gif"
    sector_label = cfg.get("sector_label", "negocio local")

    asunto = generar_asunto(lead, cfg)

    # ── CUERPO TEXTO PLANO ────────────────────────────────────────────────
    if tiene_web:
        ps_texto = f"velocidad móvil de {ps}/100" if ps else "velocidad móvil mejorable"
        cuerpo_texto = f"""Hola,

Soy Jesica, de N&G LAB Digital. Me dedico a ayudar a {sector_label}s como {nombre} a conseguir más clientes a través de internet.

He analizado vuestra presencia digital y hay tres cosas que creo que os interesa saber:

→ {dolor1}

→ {dolor2}

→ Cuando alguien le pregunta a ChatGPT o Google "mejor {sector_label} en {ciudad}", {nombre} no aparece — y vuestros competidores que trabajan el SEO sí aparecen cada vez más.

He preparado un informe gratuito con el análisis completo de vuestro caso:
{url_informe}

Si te viene bien hablar 15 minutos esta semana, escríbeme por WhatsApp:
https://wa.me/34673038773?text=Hola+Jesica,+he+visto+el+informe+de+{nombre.replace(' ', '+')}

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""
    else:
        cuerpo_texto = f"""Hola,

Soy Jesica, de N&G LAB Digital. Me dedico a ayudar a negocios locales como {nombre} a conseguir más clientes a través de internet.

He buscado vuestra presencia online y hay tres cosas que creo que os interesa saber:

→ {dolor1}

→ Con {resenas} reseñas en Google{f' y un {rating}/5' if rating else ''}, tenéis base — pero sin web propia, los clientes que buscan en Google van a la competencia que sí aparece.

→ Cuando alguien le pregunta a ChatGPT o Google "mejor {sector_label} en {ciudad}", {nombre} no aparece porque no tiene web. Esto va a ser cada vez más importante.

Si te viene bien hablar 15 minutos esta semana sobre cómo mejorar esto, escríbeme por WhatsApp:
https://wa.me/34673038773?text=Hola+Jesica,+me+interesa+saber+más+sobre+{nombre.replace(' ', '+')}

Un saludo,
Jesica Márquez
N&G LAB Digital · nglabdigital.com

---
Si no deseas recibir más emails: {url_baja}
"""

    # ── CUERPO HTML ───────────────────────────────────────────────────────
    ps_badge = ""
    if tiene_web and ps:
        color = "#EF4444" if ps < 50 else "#F59E0B" if ps < 80 else "#10B981"
        ps_badge = f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:700">{ps}/100 móvil</span>'

    boton_informe = ""
    if tiene_web:
        boton_informe = f"""
        <p style="text-align:center;margin:24px 0">
          <a href="{url_informe}"
             style="background:#C8FF00;color:#14141A;padding:12px 28px;border-radius:6px;
                    font-weight:700;font-size:15px;text-decoration:none;display:inline-block">
            Ver el análisis de {nombre}
          </a>
        </p>"""

    if tiene_web:
        intro = f"He analizado vuestra presencia digital {ps_badge} y hay tres cosas que creo que os interesa saber:"
    else:
        intro = f"He buscado vuestra presencia online y hay tres cosas que creo que os interesa saber:"

    cuerpo_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:24px 16px">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:8px;overflow:hidden;max-width:560px">

        <!-- Header -->
        <tr>
          <td style="background:#14141A;padding:20px 32px">
            <span style="color:#C8FF00;font-size:20px;font-weight:800;letter-spacing:2px">N&amp;G LAB</span>
            <span style="color:#666;font-size:12px;margin-left:12px">Digital Agency</span>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px">
            <p style="margin:0 0 16px;color:#1a1a1a">Hola,</p>

            <p style="margin:0 0 20px;color:#1a1a1a;line-height:1.6">
              Soy <strong>Jesica</strong>, de N&amp;G LAB Digital. Me dedico a ayudar a
              <strong>{sector_label}s</strong> como <strong>{nombre}</strong>
              a conseguir más clientes a través de internet.
            </p>

            <p style="margin:0 0 20px;color:#1a1a1a;line-height:1.6">{intro}</p>

            <!-- Pain points -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="margin:0 0 20px;border-left:3px solid #C8FF00">
              <tr><td style="padding:10px 16px;color:#333;line-height:1.5;font-size:14px">
                <strong>→</strong> {dolor1}
              </td></tr>
              <tr><td style="padding:10px 16px;color:#333;line-height:1.5;font-size:14px;border-top:1px solid #f0f0f0">
                <strong>→</strong> {dolor2}
              </td></tr>
              <tr><td style="padding:10px 16px;color:#333;line-height:1.5;font-size:14px;border-top:1px solid #f0f0f0">
                <strong>→</strong> Cuando alguien le pregunta a <strong>ChatGPT o Google</strong>
                "mejor {sector_label} en {ciudad}", <strong>{nombre} no aparece</strong> —
                y vuestros competidores que trabajan el SEO sí aparecen cada vez más.
              </td></tr>
            </table>

            {boton_informe}

            <p style="margin:20px 0;color:#1a1a1a;line-height:1.6">
              Si te viene bien hablar <strong>15 minutos esta semana</strong>,
              escríbeme por WhatsApp y lo organizamos sin compromiso:
            </p>

            <p style="text-align:center;margin:0 0 28px">
              <a href="https://wa.me/34673038773?text=Hola+Jesica,+he+visto+tu+email+sobre+{nombre.replace(' ', '+')}"
                 style="background:#25D366;color:#fff;padding:10px 24px;border-radius:6px;
                        font-weight:700;font-size:14px;text-decoration:none;display:inline-block">
                Escribir por WhatsApp
              </a>
            </p>

            <!-- Firma -->
            <p style="margin:0;color:#1a1a1a;line-height:1.6;border-top:1px solid #f0f0f0;padding-top:20px">
              Un saludo,<br>
              <strong>Jesica Márquez</strong><br>
              <span style="color:#666;font-size:13px">N&amp;G LAB Digital ·
                <a href="https://nglabdigital.com" style="color:#C8FF00">nglabdigital.com</a>
              </span>
            </p>
          </td>
        </tr>

        <!-- Footer LSSI -->
        <tr>
          <td style="background:#f9f9f9;padding:16px 32px;border-top:1px solid #eee;text-align:center">
            <p style="margin:0;font-size:11px;color:#999;line-height:1.6">
              Has recibido este email porque tu negocio aparece en Google Maps.<br>
              <a href="{url_baja}" style="color:#999;text-decoration:underline">
                No quiero recibir más emails
              </a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

  <!-- Pixel tracking -->
  <img src="{url_pixel}" width="1" height="1" style="display:none" alt="">
</body>
</html>"""

    return {
        "asunto": asunto,
        "cuerpo_texto": cuerpo_texto,
        "cuerpo_html": cuerpo_html,
    }


def main(nicho=None):
    leads = leads_por_estado("auditado", nicho=nicho)
    print(f"[EMAIL] {len(leads)} leads para generar email")

    ok = 0
    error = 0

    for lead in leads:
        lid    = lead.get("id")
        nombre = lead.get("nombre_negocio", "")
        n      = nicho or lead.get("sector", "otro")

        # Aseguramos que el nicho existe, si no usamos "otro"
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
            print(f"  OK  {nombre[:50]}")
        else:
            error += 1
            print(f"  ERR {nombre[:50]}")

        time.sleep(0.1)  # sin API que esperar, solo pausa de cortesía

    print(f"[EMAIL] {ok} generados · {error} errores")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
