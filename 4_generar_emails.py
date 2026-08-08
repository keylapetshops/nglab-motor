from __future__ import annotations
"""NGLAB Motor — Paso 4: Generación de emails con Claude (marca N&G LAB).

Email 1 — Intriga + informe gratis:
  - Primera línea con dato REAL del negocio (rating Google o algo concreto)
  - Pain point concreto detectado en SU web, traducido a dinero perdido
  - Intriga: "he encontrado X cosas, están en el botón"
  - NO revela los pain points en el email (eso los ve en el informe)
  - Plantilla HTML con colores N&G LAB (#14141A / #C8FF00)
  - Pixel de tracking + baja LSSI en un clic

Uso:
    python3 4_generar_emails.py
    python3 4_generar_emails.py dental
"""
import html as html_lib
import json
import sys
import time

import httpx

from config import (ANTHROPIC_API_KEY, BASE_URL, INFORMES_BASE,
                    REMITENTE_NOMBRE, REMITENTE_EMAIL, EMPRESA_LEGAL,
                    NICHOS, nicho_config)
from db import leads_por_estado, actualizar_lead, cargar_json, stats, ahora

MODELO = "claude-sonnet-4-6"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """Eres el copywriter de cold email B2B más eficaz de España.
Escribes para N&G LAB Digital, agencia de marketing digital de Valencia
(nglabdigital.com), fundada por Jesica Márquez.

Sector: {sector}.
Dolor principal del sector: {dolor}.

OBJETIVO: conseguir que el dueño pulse el botón para ver su análisis gratuito.
Ese clic es la única conversión que importa.

DATOS REALES del negocio que tienes disponibles (úsalos):
- Rating Google y número de reseñas (si los tienes, ÚSALOS en la primera línea)
- Puntuación PageSpeed móvil (si es baja, es tu mejor argumento)
- Pain points detectados (NO los reveles en el email, úsalos para crear intriga)
- Estado de la web (HTTPS, móvil, citas online, WhatsApp)

ESTRUCTURA DEL EMAIL (3 párrafos cortos):

P�rrafo 1 — PRIMERA FRASE DEMOLEDORA:
Empieza SIEMPRE con "Hola," seguido de un dato real y específico de SU negocio.
Si tiene rating: "Hola, con [N] reseñas y un [X.X] en Google se nota que en [negocio] curáis el servicio."
Si no tiene rating pero tiene web: menciona algo concreto de su sector o municipio.
Que sienta que le hablas a ÉL, no a una lista.

P�rrafo 2 — EL DOLOR (sin revelar el informe):
Menciona 1 problema concreto que hayas detectado, traducido a clientes perdidos o dinero.
Ejemplos del tono: "vuestra web tarda en cargar en el móvil y el 80% de los clientes
buscan desde el teléfono — cada segundo extra son citas que van a la clínica de al lado."
NO digas cuántos problemas has encontrado todavía.

P�rrafo 3 — LA INTRIGA + CTA:
Diles que has hecho un análisis completo de su negocio y que han salido
"varias cosas que os están costando clientes". Diles que lo ven en el botón
en 30 segundos, gratis, sin registrarse. Crea intriga, no reveles qué encontraste.
Cierra con algo corto: "Échale un vistazo, es vuestro negocio."

NORMAS:
- Español de España, tuteo, tono persona real. Nada de "estimado" ni humo corporativo.
- 70-90 palabras en total. Frases cortas. Párrafos de 1-2 líneas.
- NO pongas enlaces (el botón ya está en la plantilla HTML).
- NO uses mayúsculas gritonas ni palabras spam (gratis!!!, urgente, oferta).
- NO inventes datos que no estén en el contexto. Si no tienes rating, no lo menciones.
- Suena a persona real que ha mirado SU negocio esta mañana.

ASUNTO: máximo 6 palabras, que despierte curiosidad sobre SU negocio concreto.
Evita sonar a promoción. Ejemplos del estilo correcto:
"[Negocio], 3 cosas de vuestra web", "Una idea para [Negocio]",
"Lo que encontré en [negocio]", "Vuestro análisis digital, [Negocio]".
Usa el nombre real del negocio.

Responde SOLO con JSON válido, sin markdown ni texto extra:
{"asunto": "...", "cuerpo": "..."}"""

PIE_LEGAL = """

--
{remitente}
{empresa} · nglabdigital.com
Recibes este email como comunicación comercial B2B dirigida al buzón público de tu negocio.
Para no recibir más emails: {baja_url}"""

PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body style="margin:0;padding:0;background-color:#0d0d0d;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0d0d0d;">
<tr><td align="center" style="padding:28px 14px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;background-color:#14141A;border-radius:12px;overflow:hidden;">

  <!-- CABECERA -->
  <tr><td style="background-color:#14141A;padding:22px 32px;" align="left">
    <span style="font-family:Arial,sans-serif;font-size:21px;font-weight:700;color:#C8FF00;letter-spacing:-0.5px;">N&amp;G LAB</span>
    <span style="font-family:Arial,sans-serif;font-size:12px;color:#555;margin-left:8px;letter-spacing:1.5px;text-transform:uppercase;">Digital</span>
  </td></tr>
  <tr><td style="height:3px;background-color:#C8FF00;font-size:0;line-height:0;">&nbsp;</td></tr>

  <!-- CUERPO -->
  <tr><td style="padding:28px 32px 8px 32px;font-family:Georgia,'Times New Roman',serif;font-size:16px;line-height:1.75;color:#e0e0e0;">
{parrafos}
  </td></tr>

  <!-- CAJA ANÁLISIS GRATIS -->
  <tr><td style="padding:8px 32px 10px 32px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#1a1a24;border:1px solid #C8FF00;border-radius:8px;">
      <tr><td style="padding:18px 22px;">
        <div style="font-family:Arial,sans-serif;font-size:10px;letter-spacing:2px;color:#C8FF00;font-weight:700;margin-bottom:7px;">ANÁLISIS GRATUITO &middot; SIN COMPROMISO</div>
        <div style="font-family:Georgia,serif;color:#ffffff;font-size:17px;font-weight:bold;line-height:1.35;margin-bottom:6px;">Informe digital de {negocio}</div>
        <div style="font-family:Arial,sans-serif;color:#999;font-size:13px;line-height:1.55;">Ya está hecho. Pulsa el botón y ve en 30 segundos qué está frenando vuestro negocio online. Sin registro, sin coste, sin letra pequeña.</div>
      </td></tr>
    </table>
  </td></tr>

  <!-- BOTÓN CTA -->
  <tr><td style="padding:14px 32px 6px 32px;" align="center">
    <table role="presentation" cellpadding="0" cellspacing="0">
      <tr>
        <td style="background-color:#C8FF00;border-radius:8px;" align="center">
          <a href="{url_informe}" style="display:inline-block;padding:14px 30px;font-family:Arial,sans-serif;font-size:15px;font-weight:bold;color:#14141A;text-decoration:none;">Ver mi análisis gratis &rarr;</a>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- FIRMA -->
  <tr><td style="padding:20px 32px 26px 32px;border-top:0.5px solid #222;margin-top:16px;">
    <div style="font-family:Arial,sans-serif;font-size:14px;font-weight:600;color:#e0e0e0;margin-top:16px;">Jesica M&aacute;rquez</div>
    <div style="font-family:Arial,sans-serif;font-size:12px;color:#666;margin-top:3px;">Fundadora &middot; N&amp;G LAB Digital &middot; nglabdigital.com</div>
    <div style="font-family:Arial,sans-serif;font-size:12px;color:#444;margin-top:10px;">Co-fundadora: M&oacute;nica Sol&iacute;s</div>
  </td></tr>

</table>

<!-- PIE LEGAL -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:580px;">
  <tr><td style="padding:14px 12px;font-family:Arial,sans-serif;font-size:11px;line-height:1.5;color:#444;text-align:center;">
    {empresa_legal} &middot; nglabdigital.com<br>
    Comunicaci&oacute;n comercial B2B al buz&oacute;n p&uacute;blico de tu negocio.<br>
    <a href="{baja_url}" style="color:#444;">Darse de baja en un clic</a>
  </td></tr>
</table>
<img src="{url_pixel}" width="1" height="1" alt="" style="display:block;border:0;">
</td></tr>
</table>
</body>
</html>"""


def construir_html(cuerpo: str, baja_url: str, negocio: str,
                   url_informe: str, url_pixel: str) -> str:
    parrafos_html = []
    for parrafo in cuerpo.split("\n\n"):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        seguro = html_lib.escape(parrafo).replace("\n", "<br>")
        parrafos_html.append(f'    <p style="margin:0 0 16px 0;">{seguro}</p>')

    return PLANTILLA_HTML.format(
        parrafos="\n".join(parrafos_html),
        negocio=html_lib.escape(negocio),
        url_informe=url_informe,
        url_pixel=url_pixel,
        empresa_legal=html_lib.escape(EMPRESA_LEGAL),
        baja_url=baja_url,
    )


def redactar(lead: dict) -> dict | None:
    cfg = NICHOS.get(lead.get("sector") or "otro", NICHOS["otro"])
    auditoria = cargar_json(lead.get("auditoria")) or {}
    pain_points = cargar_json(lead.get("pain_points")) or []
    pagespeed = auditoria.get("pagespeed", {})

    system = SYSTEM_PROMPT.format(
        sector=cfg["nombre"],
        dolor=cfg["dolor"],
    )

    contexto = {
        "negocio": lead["nombre_negocio"],
        "municipio": lead.get("ciudad", ""),
        "sector": cfg["nombre"],
        "rating_google": lead.get("calificacion_google"),
        "num_resenas": lead.get("resenas_google"),
        "web": lead.get("web", ""),
        "tiene_web": bool(lead.get("web")),
        "pagespeed_mobile": pagespeed.get("puntuacion_mobile"),
        "lcp": pagespeed.get("lcp", ""),
        "pain_points_detectados": pain_points,
        "web_activa": auditoria.get("web_activa", False),
        "https": auditoria.get("https", False),
        "movil_optimizada": auditoria.get("movil_optimizada", False),
        "tiene_whatsapp": auditoria.get("tiene_whatsapp", False),
        "tiene_citas_online": auditoria.get("tiene_citas_online", False),
        "tiene_titulo_seo": auditoria.get("tiene_titulo_seo", False),
    }

    payload = {
        "model": MODELO,
        "max_tokens": 700,
        "system": system,
        "messages": [{
            "role": "user",
            "content": (
                "Redacta el Email 1 para este negocio usando los datos reales:\n"
                + json.dumps(contexto, ensure_ascii=False, indent=2)
            ),
        }],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    for intento in range(3):
        try:
            with httpx.Client(timeout=45) as c:
                r = c.post(ANTHROPIC_URL, headers=headers, json=payload)
            if r.status_code == 200:
                contenido = r.json().get("content", [])
                texto = contenido[0]["text"].strip() if contenido else ""
                if not texto:
                    return None
                if texto.startswith("```"):
                    texto = texto.strip("`").removeprefix("json").strip()
                ini, fin = texto.find("{"), texto.rfind("}")
                if ini != -1 and fin != -1:
                    texto = texto[ini:fin + 1]
                try:
                    datos = json.loads(texto)
                except json.JSONDecodeError:
                    print("  [AVISO] JSON inválido de Claude, reintentando...")
                    time.sleep(2)
                    continue
                if isinstance(datos, dict) and datos.get("asunto") and datos.get("cuerpo"):
                    return datos
                return None
            if r.status_code in (429, 529) or r.status_code >= 500:
                time.sleep(2 * (intento + 1))
                continue
            print(f"  [ERROR HTTP {r.status_code}] {r.text[:160]}")
            return None
        except httpx.HTTPError as e:
            print(f"  [ERROR red {type(e).__name__}] intento {intento + 1}/3")
            time.sleep(2 * (intento + 1))
    return None


def main(nicho: str | None = None):
    if not ANTHROPIC_API_KEY:
        print("[REDACCION] Falta ANTHROPIC_API_KEY")
        return

    if nicho is None:
        nicho = sys.argv[1].lower() if len(sys.argv) > 1 else None
    if nicho:
        nicho_config(nicho)

    # SOLO leads con email verificado — nunca mezclar con sin_email
    pendientes = [
        l for l in leads_por_estado("auditado", nicho=nicho)
        if l.get("email") and not l.get("email_invalido")
    ]
    print(f"Leads con email pendientes de redacción: {len(pendientes)}")

    for i, lead in enumerate(pendientes, 1):
        datos = redactar(lead)
        if not datos:
            print(f"[{i}/{len(pendientes)}] {lead['nombre_negocio'][:40]:40} -> FALLO")
            continue

        baja_url  = f"{BASE_URL}/baja/{lead['token_baja']}"
        url_pixel = f"{BASE_URL}/px/{lead['token_baja']}.gif"
        # El informe vive en Vercel — usamos el id del lead como slug
        url_informe = f"{INFORMES_BASE}/informe/{lead['id']}"

        cuerpo_texto = datos["cuerpo"].rstrip() + PIE_LEGAL.format(
            remitente=REMITENTE_NOMBRE,
            empresa=EMPRESA_LEGAL,
            baja_url=baja_url,
        )
        cuerpo_html = construir_html(
            datos["cuerpo"], baja_url,
            lead["nombre_negocio"], url_informe, url_pixel,
        )

        actualizar_lead(
            lead["id"],
            email_asunto=datos["asunto"][:120],
            email_cuerpo=cuerpo_texto,
            email_html=cuerpo_html,
            estado="listo_para_enviar",
            updated_at=ahora(),
        )
        print(
            f"[{i}/{len(pendientes)}] {lead['nombre_negocio'][:40]:40} "
            f"-> \"{datos['asunto']}\""
        )
        time.sleep(0.5)

    print("\nResumen:", stats())


if __name__ == "__main__":
    main()
