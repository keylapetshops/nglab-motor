"""NGLAB Motor — Generador de informes HTML por lead.

Mejoras vs versión anterior:
- Bloque de presupuesto con descuento (-40%) y número real
- Checklist visual de qué tiene / qué le falta la web
- Problemas numerados con solución y precio por cada uno
- CTA doble: WhatsApp + Calendly
- cls_val y fid ahora aparecen en el HTML
"""
import json
import os
import httpx
from db import leads_por_estado, actualizar_lead, ahora
from config import BASE_URL

MOTOR_URL = os.getenv("MOTOR_URL", "https://nglab-motor-production.up.railway.app")
WHATSAPP_NUM = "34673038773"
CALENDLY_URL = "https://calendly.com/hola-nglabdigital/30min"

# Precios reales de N&G LAB (nglabdigital.com/precios) — precio de mercado antes del descuento
PRECIOS = {
    "web_basica":        ("Landing Express — web profesional de una página",  597),
    "web_profesional":   ("Web Profesional — multi-sección a medida",        1197),
    "seo_local":         ("Visibilidad Digital · SEO local + Google Maps",    397),
    "reservas_online":   ("Sistema de reservas/citas online con Orbo",        149),  # Orbo Start/mes
    "whatsapp_business": ("Canal WhatsApp Business automatizado",             197),  # Redes Start/mes
    "velocidad_web":     ("Optimización técnica web y PageSpeed",             397),
    "https":             ("Certificado HTTPS + SEO básico incluido",          197),
    "ia_visibilidad":    ("Visibilidad en IA · GEO (ChatGPT, Gemini...)",    397),
}

DESCUENTO = 0.40  # 40% — precio especial primer contacto


def _circulo(score, label):
    if score is None or score == "" or score == 0:
        color = "#444"
        texto = "N/A"
        dash = 0
    else:
        s = int(score)
        texto = str(s)
        dash = s
        color = "#10B981" if s >= 90 else "#F59E0B" if s >= 50 else "#EF4444"

    return f"""
    <div class="circle-wrap">
        <svg viewBox="0 0 36 36" class="circle-svg">
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#2a2a35" stroke-width="3"/>
            <circle cx="18" cy="18" r="15.9" fill="none" stroke="{color}" stroke-width="3"
                stroke-dasharray="{dash} 100"
                stroke-dashoffset="25" stroke-linecap="round" transform="rotate(-90 18 18)"/>
            <text x="18" y="20.5" text-anchor="middle" fill="{color}"
                font-size="7" font-weight="700">{texto}</text>
        </svg>
        <p class="circle-label">{label}</p>
    </div>"""


def _estrellas(rating):
    if not rating:
        return ""
    r = float(rating)
    stars = ""
    for i in range(1, 6):
        color = "#F59E0B" if r >= i - 0.5 else "#444"
        stars += f'<span style="color:{color}">★</span>'
    return stars


def _pill(ok: bool, texto: str) -> str:
    if ok:
        return f'<span class="pill pill-ok">✓ {texto}</span>'
    else:
        return f'<span class="pill pill-no">✗ {texto}</span>'


def _calcular_presupuesto(lead: dict, auditoria: dict, pain_points: list) -> tuple[list, int, int]:
    """Devuelve (servicios_necesarios, precio_mercado, precio_con_descuento)."""
    servicios = []
    web = lead.get("web", "")
    tiene_web = bool(web and web.strip())
    ps = auditoria.get("pagespeed") or {}
    rendimiento = ps.get("puntuacion_mobile") or 0

    if not tiene_web:
        servicios.append("web_basica")
        servicios.append("seo_local")
        servicios.append("ia_visibilidad")
    else:
        if rendimiento and int(rendimiento) < 70:
            servicios.append("velocidad_web")
        if not auditoria.get("https"):
            servicios.append("https")
        if not auditoria.get("tiene_citas_online"):
            servicios.append("reservas_online")
        if not auditoria.get("tiene_whatsapp"):
            servicios.append("whatsapp_business")
        servicios.append("seo_local")
        servicios.append("ia_visibilidad")

    # Máximo 4 servicios
    servicios = list(dict.fromkeys(servicios))[:4]

    precio_mercado = sum(PRECIOS[s][1] for s in servicios)
    precio_final = int(precio_mercado * (1 - DESCUENTO))
    return servicios, precio_mercado, precio_final


def generar_html(lead: dict) -> str:
    nombre = lead.get("nombre_negocio", "Tu negocio")
    web = lead.get("web", "")
    ciudad = lead.get("ciudad", "")
    sector = lead.get("sector", "")
    rating = lead.get("calificacion_google")
    resenas = lead.get("resenas_google") or 0
    pain_points = lead.get("pain_points") or []
    lead_id = lead.get("id", "")
    token = lead.get("token_baja", "")

    if isinstance(pain_points, str):
        try:
            pain_points = json.loads(pain_points)
        except:
            pain_points = []

    auditoria_raw = lead.get("auditoria") or {}
    if isinstance(auditoria_raw, str):
        try:
            auditoria_raw = json.loads(auditoria_raw)
        except:
            auditoria_raw = {}

    ps = auditoria_raw.get("pagespeed") or {}
    rendimiento = lead.get("pagespeed_mobile") or ps.get("puntuacion_mobile") or 0
    fcp = ps.get("fcp", "N/A")
    lcp = ps.get("lcp", "N/A")
    cls_val = ps.get("cls", "N/A")
    fid = ps.get("fid", "N/A")
    accesib = ps.get("accesibilidad") or auditoria_raw.get("accesibilidad") or None
    buenas = ps.get("buenas_practicas") or auditoria_raw.get("buenas_practicas") or None
    seo_score = ps.get("seo") or auditoria_raw.get("seo") or None

    tiene_web = bool(web and web.strip())
    tiene_https = auditoria_raw.get("https", False)
    tiene_movil = auditoria_raw.get("movil_optimizada", False)
    tiene_citas = auditoria_raw.get("tiene_citas_online", False)
    tiene_whatsapp = auditoria_raw.get("tiene_whatsapp", False)
    tiene_instagram = auditoria_raw.get("tiene_instagram", False)
    tiene_seo_titulo = auditoria_raw.get("tiene_titulo_seo", False)
    tiene_seo_desc = auditoria_raw.get("tiene_meta_descripcion", False)

    # Presupuesto
    servicios, precio_mercado, precio_final = _calcular_presupuesto(lead, auditoria_raw, pain_points)

    # Pain points HTML numerados con solución
    pp_html = ""
    for i, p in enumerate(pain_points[:4], 1):
        if isinstance(p, dict):
            p = p.get("label") or p.get("code") or str(p)
        # Buscar si hay un servicio relacionado
        solucion = ""
        if "reserva" in p.lower() or "cita" in p.lower():
            solucion = "→ Solución: Sistema de reservas/citas online con confirmación automática"
        elif "whatsapp" in p.lower():
            solucion = "→ Solución: Canal WhatsApp Business con botón visible en web"
        elif "velocidad" in p.lower() or "móvil" in p.lower() or "movil" in p.lower():
            solucion = "→ Solución: Optimización técnica web y PageSpeed"
        elif "https" in p.lower() or "segur" in p.lower():
            solucion = "→ Solución: Certificado SSL + configuración HTTPS"
        elif "seo" in p.lower() or "google" in p.lower() or "visib" in p.lower():
            solucion = "→ Solución: SEO local + posicionamiento en Google Maps"
        elif "web" in p.lower():
            solucion = "→ Solución: Web profesional optimizada para móvil y Google"

        pp_html += f"""
        <div class="problema">
            <div class="problema-header">
                <span class="problema-num">⚠ PROBLEMA {i}</span>
            </div>
            <p class="problema-texto">{p}</p>
            {f'<p class="problema-solucion">{solucion}</p>' if solucion else ''}
        </div>"""

    if not pp_html:
        pp_html = '<div class="problema"><p class="problema-texto">Análisis pendiente</p></div>'

    # Checklist
    checklist_html = f"""
    <div class="checklist">
        {_pill(tiene_web, "Web activa y accesible")}
        {_pill(tiene_https, "Conexión segura (HTTPS)")}
        {_pill(tiene_movil, "Optimizada para móvil")}
        {_pill(tiene_citas, "Reservas / citas online")}
        {_pill(tiene_whatsapp, "Canal de WhatsApp en la web")}
        {_pill(tiene_instagram, "Instagram enlazado")}
        {_pill(tiene_seo_titulo, "SEO básico (título)")}
        {_pill(tiene_seo_desc, "SEO básico (descripción)")}
    </div>"""

    # Rating HTML
    rating_html = ""
    if rating:
        badge = "Excelente reputación" if float(rating) >= 4.5 else "Buena reputación" if float(rating) >= 4.0 else "Mejorable"
        rating_html = f"""
        <div class="gb-rating">
            <span class="gb-score">{rating}</span>
            <div>
                <div class="gb-stars">{_estrellas(rating)}</div>
                <p class="gb-resenas">{resenas} reseñas en Google</p>
                <span class="gb-badge">{badge}</span>
            </div>
        </div>"""

    # Bloque presupuesto
    servicios_html = ""
    for s in servicios:
        nombre_s, precio_s = PRECIOS[s]
        precio_dto = int(precio_s * (1 - DESCUENTO))
        servicios_html += f"""
        <div class="presup-linea">
            <span class="presup-nombre">{nombre_s}</span>
            <span class="presup-precio">
                <span class="precio-tachado">{precio_s}€</span>
                <span class="precio-final">{precio_dto}€</span>
            </span>
        </div>"""

    wa_texto = f"Hola Jesica, he visto mi informe de {nombre} y quiero saber más".replace(" ", "%20")
    wa_url = f"https://wa.me/{WHATSAPP_NUM}?text={wa_texto}"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Análisis digital gratuito · {nombre}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background:#14141A; color:#e8e8e8; font-family:'Segoe UI',system-ui,sans-serif; }}

.header {{ background:#14141A; border-bottom:2px solid #C8FF00; padding:20px 32px; display:flex; align-items:center; gap:16px; }}
.logo {{ color:#C8FF00; font-size:22px; font-weight:800; letter-spacing:2px; }}
.header-sub {{ color:#888; font-size:13px; text-transform:uppercase; letter-spacing:1px; }}
.header-badge {{ margin-left:auto; background:#C8FF00; color:#14141A; font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px; }}

.hero {{ background:#1a1a24; padding:40px 32px 32px; border-bottom:1px solid #2a2a35; }}
.hero-label {{ color:#C8FF00; font-size:12px; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }}
.hero h1 {{ font-size:26px; font-weight:800; color:#fff; margin-bottom:6px; }}
.hero p {{ color:#888; font-size:14px; }}

.section {{ padding:28px 32px; border-bottom:1px solid #1e1e2a; }}
.section-title {{ color:#C8FF00; font-size:13px; font-weight:700; text-transform:uppercase;
    letter-spacing:2px; margin-bottom:20px; display:flex; align-items:center; gap:8px; }}

/* Checklist */
.checklist {{ display:flex; flex-wrap:wrap; gap:8px; }}
.pill {{ font-size:12px; font-weight:600; padding:6px 12px; border-radius:20px; }}
.pill-ok {{ background:#0d2e1a; color:#10B981; border:1px solid #10B981; }}
.pill-no {{ background:#2e1010; color:#EF4444; border:1px solid #EF4444; }}

/* Círculos */
.circles {{ display:flex; gap:20px; flex-wrap:wrap; justify-content:center; }}
.circle-wrap {{ text-align:center; width:90px; }}
.circle-svg {{ width:80px; height:80px; }}
.circle-label {{ font-size:11px; color:#888; margin-top:6px; }}

.metrics-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:20px; }}
.metric-box {{ background:#1e1e2a; border-radius:8px; padding:14px; text-align:center; }}
.metric-box .val {{ font-size:18px; font-weight:700; color:#C8FF00; }}
.metric-box .lbl {{ font-size:11px; color:#666; margin-top:4px; }}

/* Rating */
.gb-rating {{ display:flex; align-items:center; gap:16px; }}
.gb-score {{ font-size:52px; font-weight:800; color:#C8FF00; line-height:1; }}
.gb-stars {{ font-size:22px; margin-bottom:4px; }}
.gb-resenas {{ font-size:13px; color:#888; }}
.gb-badge {{ display:inline-block; margin-top:6px; background:#C8FF00; color:#14141A;
    font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; }}

/* Problemas */
.problema {{ background:#1e1e2a; border:1px solid #2a2a35; border-radius:8px;
    padding:16px; margin-bottom:12px; border-left:3px solid #EF4444; }}
.problema-header {{ margin-bottom:8px; }}
.problema-num {{ font-size:11px; font-weight:700; color:#EF4444; letter-spacing:1px; }}
.problema-texto {{ font-size:13px; color:#ccc; line-height:1.6; margin-bottom:8px; }}
.problema-solucion {{ font-size:12px; color:#10B981; font-weight:600; }}

/* IA */
.ia-box {{ background:#1e1e2a; border:1px solid #2a2a35; border-radius:8px; padding:20px; }}
.ia-box p {{ font-size:13px; color:#aaa; line-height:1.7; }}
.ia-box strong {{ color:#C8FF00; }}

/* Presupuesto */
.presup-box {{ background:#1a1a24; border:2px solid #C8FF00; border-radius:12px; padding:28px; }}
.presup-label {{ color:#C8FF00; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:2px; margin-bottom:16px; text-align:center; }}
.presup-linea {{ display:flex; justify-content:space-between; align-items:center;
    padding:12px 0; border-bottom:1px solid #2a2a35; }}
.presup-linea:last-of-type {{ border-bottom:none; }}
.presup-nombre {{ font-size:13px; color:#ccc; }}
.presup-precio {{ display:flex; align-items:center; gap:8px; }}
.precio-tachado {{ font-size:13px; color:#555; text-decoration:line-through; }}
.precio-final {{ font-size:15px; font-weight:700; color:#C8FF00; }}
.presup-total {{ margin-top:20px; background:#C8FF00; border-radius:8px; padding:18px 20px; text-align:center; }}
.presup-total-label {{ font-size:12px; font-weight:700; color:#14141A; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px; }}
.presup-total-precio {{ font-size:36px; font-weight:800; color:#14141A; line-height:1; }}
.presup-total-antes {{ font-size:14px; color:#555; text-decoration:line-through; margin-top:4px; }}
.presup-nota {{ font-size:11px; color:#14141A; margin-top:8px; opacity:0.7; }}
.presup-razon {{ margin-top:20px; background:#1e1e2a; border-radius:8px; padding:16px; }}
.presup-razon p {{ font-size:12px; color:#888; line-height:1.7; }}
.presup-razon strong {{ color:#C8FF00; }}

/* CTA */
.cta {{ background:#1a1a24; padding:36px 32px; text-align:center; border-top:2px solid #C8FF00; }}
.cta h2 {{ color:#fff; font-size:20px; font-weight:800; margin-bottom:8px; }}
.cta p {{ color:#888; font-size:13px; margin-bottom:24px; }}
.cta-btns {{ display:flex; flex-direction:column; gap:12px; align-items:center; }}
.btn-primary {{ display:inline-block; background:#C8FF00; color:#14141A;
    padding:15px 36px; font-size:15px; font-weight:800; border-radius:6px;
    text-decoration:none; width:100%; max-width:360px; }}
.btn-secondary {{ display:inline-block; background:transparent; color:#C8FF00;
    border:2px solid #C8FF00; padding:13px 36px; font-size:14px; font-weight:700;
    border-radius:6px; text-decoration:none; width:100%; max-width:360px; }}
.cta-footer {{ margin-top:16px; font-size:11px; color:#555; }}

.footer {{ padding:20px 32px; text-align:center; font-size:11px; color:#444; }}

@media(max-width:500px) {{
    .hero h1 {{ font-size:20px; }}
    .circles {{ gap:12px; }}
    .circle-wrap {{ width:72px; }}
    .section {{ padding:20px 20px; }}
    .header {{ padding:16px 20px; }}
    .cta {{ padding:28px 20px; }}
    .presup-box {{ padding:20px; }}
}}
</style>
</head>
<body>

<div class="header">
    <div>
        <div class="logo">N&amp;G LAB</div>
        <div class="header-sub">Análisis Digital Gratuito</div>
    </div>
    <span class="header-badge">Informe personalizado</span>
</div>

<div class="hero">
    <div class="hero-label">Análisis digital gratuito</div>
    <h1>{nombre}</h1>
    <p>{web or 'Sin página web propia'}{f' · {ciudad}' if ciudad else ''}{f' · {sector}' if sector else ''}</p>
</div>

<!-- Estado actual -->
<div class="section">
    <div class="section-title">✓ Estado actual de tu presencia digital</div>
    {checklist_html}
</div>

<!-- PageSpeed -->
{'<div class="section"><div class="section-title">⚡ Velocidad web · Mobile</div><div class="circles">' + _circulo(rendimiento, "Rendimiento") + _circulo(accesib, "Accesibilidad") + _circulo(buenas, "Buenas prácticas") + _circulo(seo_score, "SEO") + '</div><div class="metrics-grid"><div class="metric-box"><div class="val">' + str(fcp) + '</div><div class="lbl">First Contentful Paint</div></div><div class="metric-box"><div class="val">' + str(lcp) + '</div><div class="lbl">Largest Contentful Paint</div></div><div class="metric-box"><div class="val">' + str(cls_val) + '</div><div class="lbl">Cumulative Layout Shift</div></div><div class="metric-box"><div class="val">' + str(fid) + '</div><div class="lbl">Total Blocking Time</div></div></div></div>' if tiene_web else ''}

<!-- Google Business -->
{'<div class="section"><div class="section-title">⭐ Google Business</div>' + rating_html + '</div>' if rating else ''}

<!-- Problemas detectados -->
<div class="section">
    <div class="section-title">🎯 Lo que hemos encontrado (y cómo lo arreglamos)</div>
    <p style="font-size:13px;color:#888;margin-bottom:18px">Estos {len(pain_points[:4])} puntos son los que ahora mismo te están costando clientes:</p>
    {pp_html}
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

<!-- Presupuesto -->
<div class="section">
    <div class="section-title">💰 Presupuesto estimado · Descuento 40% aplicado</div>
    <div class="presup-box">
        <div class="presup-label">Solución completa para {nombre}</div>
        {servicios_html}
        <div class="presup-total">
            <div class="presup-total-label">Precio con descuento aplicado</div>
            <div class="presup-total-precio">{precio_final}€</div>
            <div class="presup-total-antes">precio de mercado: {precio_mercado}€</div>
            <div class="presup-nota">Es una estimación orientativa. El precio final lo cerramos juntos según lo que de verdad necesites — sin pagar de más por cosas que no usas.</div>
        </div>
        <div class="presup-razon">
            <p>🏠 <strong>¿Por qué puedo ofrecerte estos precios?</strong><br>
            Trabajo desde mi ordenador, sin oficina, sin empleados y sin infraestructura que pagar.
            Eso significa que <strong>mis precios son siempre de los más económicos del mercado</strong>
            — te llega el ahorro directo a ti, con trato personal conmigo, la fundadora.</p>
        </div>
    </div>
    <p style="font-size:12px;color:#555;margin-top:14px;text-align:center">
        ✅ Instalado y funcionando en 72 horas · Trato directo con Jesica, sin comerciales
    </p>
</div>

<!-- CTA -->
<div class="cta">
    <h2>¿Quieres mejorar estos puntos?</h2>
    <p>15 minutos de llamada · Sin compromiso · Elige cómo prefieres</p>
    <div class="cta-btns">
        <a href="{wa_url}" class="btn-primary">💬 Quiero hablar con Jesica</a>
        <a href="{CALENDLY_URL}" class="btn-secondary">📅 O agenda una llamada de 10 min aquí</a>
    </div>
    <p class="cta-footer">🖨️ <a href="javascript:window.print()" style="color:#555;text-decoration:underline">Imprimir o guardar como PDF</a></p>
</div>

<div class="footer">
    N&amp;G LAB Digital · hola@nglabdigital.com · Este informe es confidencial y ha sido generado exclusivamente para {nombre}.
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
        lid = lead.get("id")
        nombre = lead.get("nombre_negocio", "lead")
        slug = str(lid)
        html = generar_html(lead)
        url = subir_a_supabase(slug, html)
        if url:
            actualizar_lead(lid, url_informe=url, estado="informe_generado")
            print(f"   ✓ {nombre} → {url}")
        else:
            print(f"   ✗ {nombre} → error al subir")


if __name__ == "__main__":
    main()
