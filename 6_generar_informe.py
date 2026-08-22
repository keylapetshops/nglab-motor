"""NGLAB Motor — Generador de informes HTML por lead."""
import json
import os
import httpx
from db import leads_por_estado, actualizar_lead, ahora
from config import BASE_URL

MOTOR_URL = os.getenv("MOTOR_URL", "https://nglab-motor-production.up.railway.app")


def _circulo(score, label):
    """Genera SVG de círculo con puntuación."""
    if score is None or score == "" or score == 0:
        color = "#444"
        texto = "N/A"
    else:
        s = int(score)
        texto = str(s)
        if s >= 90:
            color = "#10B981"
        elif s >= 50:
            color = "#F59E0B"
        else:
            color = "#EF4444"

    return f"""
    <div class="circle-wrap">
      <svg viewBox="0 0 36 36" class="circle-svg">
        <circle cx="18" cy="18" r="15.9" fill="none" stroke="#2a2a35" stroke-width="3"/>
        <circle cx="18" cy="18" r="15.9" fill="none" stroke="{color}" stroke-width="3"
          stroke-dasharray="{int(score) if score and score != 'N/A' else 0} 100"
          stroke-dashoffset="25" stroke-linecap="round" transform="rotate(-90 18 18)"/>
        <text x="18" y="20.5" text-anchor="middle" fill="{color}"
          font-size="7" font-weight="700">{texto}</text>
      </svg>
      <p class="circle-label">{label}</p>
    </div>"""


def _estrellas(rating):
    """Genera estrellas HTML para el rating."""
    if not rating:
        return ""
    r = float(rating)
    stars = ""
    for i in range(1, 6):
        if r >= i:
            stars += '<span style="color:#F59E0B">★</span>'
        elif r >= i - 0.5:
            stars += '<span style="color:#F59E0B">★</span>'
        else:
            stars += '<span style="color:#444">★</span>'
    return stars


def generar_html(lead: dict) -> str:
    nombre     = lead.get("nombre_negocio", "Tu negocio")
    web        = lead.get("web", "")
    ciudad     = lead.get("ciudad", "")
    sector     = lead.get("sector", "")
    rating     = lead.get("calificacion_google")
    resenas    = lead.get("resenas_google") or 0
    pain_points = lead.get("pain_points") or []
    if isinstance(pain_points, str):
        try: pain_points = json.loads(pain_points)
        except: pain_points = []

    # Datos auditoria
    auditoria_raw = lead.get("auditoria") or {}
    if isinstance(auditoria_raw, str):
        try: auditoria_raw = json.loads(auditoria_raw)
        except: auditoria_raw = {}

    ps          = auditoria_raw.get("pagespeed") or {}
    rendimiento = lead.get("pagespeed_mobile") or ps.get("puntuacion_mobile") or 0
    fcp         = ps.get("fcp", "N/A")
    lcp         = ps.get("lcp", "N/A")
    cls_val     = ps.get("cls", "N/A")
    fid         = ps.get("fid", "N/A")

    # Accesibilidad, buenas prácticas, SEO — están dentro de pagespeed, no en auditoria_raw
    accesib   = ps.get("accesibilidad") or auditoria_raw.get("accesibilidad") or None
    buenas    = ps.get("buenas_practicas") or auditoria_raw.get("buenas_practicas") or None
    seo_score = ps.get("seo") or auditoria_raw.get("seo") or None

    # Pain points HTML
    pp_html = ""
    for p in pain_points[:4]:
        if isinstance(p, dict):
            p = p.get("label") or p.get("code") or str(p)
        pp_html += f'<li>⚠️ {p}</li>\n'
    if not pp_html:
        pp_html = '<li style="color:#666">Análisis pendiente</li>'

    # Rating Google
    rating_html = ""
    if rating:
        rating_html = f"""
        <div class="gb-rating">
          <span class="gb-score">{rating}</span>
          <div>
            <div class="gb-stars">{_estrellas(rating)}</div>
            <p class="gb-resenas">{resenas} reseñas en Google</p>
            <span class="gb-badge">{'Excelente reputación' if float(rating) >= 4.5 else 'Buena reputación' if float(rating) >= 4.0 else 'Mejorable'}</span>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Análisis digital · {nombre}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background:#14141A; color:#e8e8e8; font-family:'Segoe UI',system-ui,sans-serif; }}

    .header {{ background:#14141A; border-bottom:2px solid #C8FF00; padding:20px 32px; display:flex; align-items:center; gap:16px; }}
    .logo {{ color:#C8FF00; font-size:22px; font-weight:800; letter-spacing:2px; }}
    .header-sub {{ color:#888; font-size:13px; text-transform:uppercase; letter-spacing:1px; }}

    .hero {{ background:#1a1a24; padding:40px 32px 32px; border-bottom:1px solid #2a2a35; }}
    .hero-label {{ color:#C8FF00; font-size:12px; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }}
    .hero h1 {{ font-size:26px; font-weight:800; color:#fff; margin-bottom:6px; }}
    .hero p {{ color:#888; font-size:14px; }}

    .section {{ padding:28px 32px; border-bottom:1px solid #1e1e2a; }}
    .section-title {{ color:#C8FF00; font-size:13px; font-weight:700; text-transform:uppercase;
                      letter-spacing:2px; margin-bottom:20px; display:flex; align-items:center; gap:8px; }}

    /* Círculos PageSpeed */
    .circles {{ display:flex; gap:20px; flex-wrap:wrap; justify-content:center; }}
    .circle-wrap {{ text-align:center; width:90px; }}
    .circle-svg {{ width:80px; height:80px; }}
    .circle-label {{ font-size:11px; color:#888; margin-top:6px; }}

    .metrics-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:20px; }}
    .metric-box {{ background:#1e1e2a; border-radius:8px; padding:14px; text-align:center; }}
    .metric-box .val {{ font-size:18px; font-weight:700; color:#C8FF00; }}
    .metric-box .lbl {{ font-size:11px; color:#666; margin-top:4px; }}

    /* Google Business */
    .gb-rating {{ display:flex; align-items:center; gap:16px; }}
    .gb-score {{ font-size:52px; font-weight:800; color:#C8FF00; line-height:1; }}
    .gb-stars {{ font-size:22px; margin-bottom:4px; }}
    .gb-resenas {{ font-size:13px; color:#888; }}
    .gb-badge {{ display:inline-block; margin-top:6px; background:#C8FF00; color:#14141A;
                 font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }}

    /* Pain points */
    .pp-list {{ list-style:none; display:flex; flex-direction:column; gap:10px; }}
    .pp-list li {{ background:#1e1e2a; border:1px solid #2a2a35; border-radius:8px;
                   padding:12px 16px; font-size:13px; color:#ccc; line-height:1.5; }}

    /* IA */
    .ia-box {{ background:#1e1e2a; border:1px solid #2a2a35; border-radius:8px; padding:20px; }}
    .ia-box p {{ font-size:13px; color:#aaa; line-height:1.7; }}
    .ia-box strong {{ color:#C8FF00; }}

    /* CTA */
    .cta {{ background:#C8FF00; padding:36px 32px; text-align:center; }}
    .cta h2 {{ color:#14141A; font-size:20px; font-weight:800; margin-bottom:16px; }}
    .cta a {{ display:inline-block; background:#14141A; color:#C8FF00; border:2px solid #14141A;
              padding:14px 36px; font-size:15px; font-weight:700; border-radius:6px;
              text-decoration:none; }}
    .footer {{ padding:20px 32px; text-align:center; font-size:11px; color:#444; }}

    @media(max-width:500px) {{
      .hero h1 {{ font-size:20px; }}
      .circles {{ gap:12px; }}
      .circle-wrap {{ width:72px; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <div class="logo">N&amp;G LAB</div>
    <div class="header-sub">Análisis Web Express</div>
  </div>
</div>

<div class="hero">
  <div class="hero-label">Informe personalizado</div>
  <h1>{nombre}</h1>
  <p>{web or 'Sin página web'}{f' · {ciudad}' if ciudad else ''}{f' · {sector}' if sector else ''}</p>
</div>

<!-- PageSpeed -->
<div class="section">
  <div class="section-title">⚡ Velocidad web · Mobile</div>
  <div class="circles">
    {_circulo(rendimiento, "Rendimiento")}
    {_circulo(accesib, "Accesibilidad")}
    {_circulo(buenas, "Buenas prácticas")}
    {_circulo(seo_score, "SEO")}
  </div>
  <div class="metrics-grid">
    <div class="metric-box"><div class="val">{fcp}</div><div class="lbl">First Contentful Paint</div></div>
    <div class="metric-box"><div class="val">{lcp}</div><div class="lbl">Largest Contentful Paint</div></div>
  </div>
</div>

<!-- Google Business -->
{'<div class="section"><div class="section-title">⭐ Google Business</div>' + rating_html + '</div>' if rating else ''}

<!-- Puntos de mejora -->
<div class="section">
  <div class="section-title">🎯 Puntos de mejora detectados</div>
  <ul class="pp-list">{pp_html}</ul>
</div>

<!-- Visibilidad en IA -->
<div class="section">
  <div class="section-title">🤖 Visibilidad en inteligencias artificiales</div>
  <div class="ia-box">
    <p>Cuando alguien le pregunta a <strong>ChatGPT, Gemini o Perplexity</strong>
    "{f'mejor {sector} en {ciudad}' if sector and ciudad else 'negocios locales recomendados'}",
    tu negocio <strong>no aparece</strong> en las respuestas.</p>
    <p style="margin-top:12px">Los negocios que trabajan el SEO y la presencia digital
    están empezando a aparecer en estas búsquedas por IA, que crecen cada mes.
    Esta es la <strong>próxima gran oportunidad</strong> para captar clientes.</p>
  </div>
</div>

<!-- CTA -->
<div class="cta">
  <h2>¿Quieres mejorar estos puntos?</h2>
  <a href="https://wa.me/34673038773?text=Hola%2C+he+visto+mi+informe+de+{nombre.replace(' ','%20')}+y+quiero+saber+m%C3%A1s">
    Hablar con Jesica por WhatsApp
  </a>
</div>

<div class="footer">
  N&amp;G LAB · hola@nglabdigital.com · Este informe es confidencial y ha sido generado exclusivamente para {nombre}.
</div>

</body>
</html>"""


def subir_a_supabase(slug: str, html: str) -> str | None:
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    url_supabase = os.getenv("SUPABASE_URL", "")
    upload_url = f"{url_supabase}/storage/v1/object/informes/{slug}/index.html"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "text/html; charset=utf-8",
        "x-upsert": "true"
    }
    with httpx.Client(timeout=30) as c:
        r = c.post(upload_url, content=html.encode("utf-8"), headers=headers)
        if r.status_code in (200, 201):
            return f"{url_supabase}/storage/v1/object/public/informes/{slug}/index.html"
    return None


def main():
    leads = leads_por_estado("auditado")
    if not leads:
        leads = leads_por_estado("pendiente_revision")
    print(f"[INFORME] {len(leads)} leads para generar informe")
    for lead in leads:
        lid    = lead.get("id")
        nombre = lead.get("nombre_negocio", "lead")
        slug   = str(lid)
        html   = generar_html(lead)
        url    = subir_a_supabase(slug, html)
        if url:
            actualizar_lead(lid, url_informe=url, estado="informe_generado")
            print(f"  ✓ {nombre} → {url}")
        else:
            print(f"  ✗ {nombre} → error al subir")


if __name__ == "__main__":
    main()
