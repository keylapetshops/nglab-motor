"""NGLAB Motor - Generador de informes HTML por lead."""
import os
import httpx
from db import _headers, _url, leads_por_estado, actualizar_lead, ahora
from config import BASE_URL

STORAGE_URL = os.getenv("SUPABASE_URL") + "/storage/v1/object/informes"
STORAGE_PUBLIC = os.getenv("SUPABASE_URL") + "/storage/v1/object/public/informes"

def generar_html(lead: dict) -> str:
    nombre = lead.get("nombre_negocio", "Tu negocio")
    web = lead.get("web", "")
    ciudad = lead.get("ciudad", "")
    sector = lead.get("sector", "")
    ps = lead.get("pagespeed_mobile", 0) or 0
    dolores = lead.get("pain_points") or []
    if isinstance(dolores, str):
        import json
        try: dolores = json.loads(dolores)
        except: dolores = []

    color_ps = "#C8FF00" if ps >= 70 else "#ff9800" if ps >= 40 else "#f44336"
    dolores_html = "".join(f'<li style="margin:8px 0;color:#ccc;">⚠️ {d}</li>' for d in dolores[:4])

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Análisis web · {nombre}</title>
<style>
body{{margin:0;font-family:'Segoe UI',sans-serif;background:#14141A;color:#fff}}
.header{{background:#14141A;padding:32px;border-bottom:2px solid #C8FF00}}
.logo{{color:#C8FF00;font-size:24px;font-weight:700;letter-spacing:2px}}
.hero{{padding:40px 32px;background:#1a1a24}}
.hero h1{{font-size:28px;margin:0 0 8px}}
.hero p{{color:#aaa;margin:0}}
.score-box{{background:#14141A;border:2px solid {color_ps};border-radius:12px;padding:24px;margin:32px;text-align:center}}
.score-num{{font-size:72px;font-weight:700;color:{color_ps};line-height:1}}
.score-label{{color:#aaa;margin-top:8px}}
.section{{padding:24px 32px}}
.section h2{{color:#C8FF00;font-size:18px;margin:0 0 16px}}
ul{{padding-left:20px;margin:0}}
.cta{{background:#C8FF00;color:#14141A;padding:32px;text-align:center;margin:32px}}
.cta h2{{font-size:24px;margin:0 0 16px}}
.btn{{background:#14141A;color:#C8FF00;border:2px solid #14141A;padding:14px 32px;font-size:16px;font-weight:700;border-radius:6px;text-decoration:none;display:inline-block}}
.footer{{padding:24px 32px;color:#666;font-size:12px;text-align:center}}
</style>
</head>
<body>
<div class="header"><div class="logo">N&G LAB</div></div>
<div class="hero">
  <h1>Análisis digital de {nombre}</h1>
  <p>{ciudad} · {sector}</p>
</div>
<div class="score-box">
  <div class="score-num">{int(ps)}</div>
  <div class="score-label">Velocidad web (PageSpeed Mobile) · máximo 100</div>
</div>
<div class="section">
  <h2>Puntos de mejora detectados</h2>
  <ul>{dolores_html if dolores_html else '<li style="color:#aaa">Análisis pendiente</li>'}</ul>
</div>
<div class="cta">
  <h2>¿Quieres saber cómo mejorar estos puntos?</h2>
  <a class="btn" href="https://wa.me/34673038773?text=Hola%2C%20he%20visto%20mi%20informe%20de%20{nombre.replace(' ','%20')}%20y%20quiero%20saber%20más">Hablar con Jesica por WhatsApp</a>
</div>
<div class="footer">N&G LAB · hola@nglabdigital.com · Este informe es confidencial y ha sido generado exclusivamente para {nombre}.</div>
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
            print(f"  ✓ {nombre} → {url}")
        else:
            print(f"  ✗ {nombre} → error al subir")

if __name__ == "__main__":
    main()
