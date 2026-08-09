from __future__ import annotations
import json, sys, time, httpx
from config import ANTHROPIC_API_KEY, INFORMES_BASE, nicho_config
from db import leads_por_estado, actualizar_lead, cargar_json

MODELO = "claude-sonnet-4-5"
URL = "https://api.anthropic.com/v1/messages"

def generar(lead, nicho):
    cfg = nicho_config(nicho)
    nombre = lead.get("nombre_negocio", "")
    ciudad = lead.get("ciudad", "")
    web = lead.get("web", "")
    tiene_web = bool(web and web.strip())
    ps = int(lead.get("pagespeed_mobile", 0) or 0)
    dolores = cargar_json(lead.get("pain_points")) or []
    dolor1 = dolores[0] if len(dolores) > 0 else ""
    dolor2 = dolores[1] if len(dolores) > 1 else ""
    dolor3 = dolores[2] if len(dolores) > 2 else ""
    url = lead.get("url_informe", f"{INFORMES_BASE}/{lead.get('id')}")
    rating = lead.get("calificacion_google", "")
    resenas = lead.get("resenas_google", "")
    sector_label = cfg.get("sector_label", "negocios")

    if tiene_web:
        contexto = f"""CASO: CON WEB ({web})
PageSpeed movil: {ps}/100. Rating Google: {rating}. Resenas: {resenas}.
Pain points detectados:
1. {dolor1}
2. {dolor2}
3. {dolor3}
URL del informe: {url}

Los tres puntos con flecha deben basarse en los pain points reales de su web.
CTA principal: "Ver mi analisis gratuito" con enlace al informe.
"""
    else:
        contexto = f"""CASO: SIN WEB
Rating Google: {rating}. Resenas: {resenas}.
Este negocio NO tiene pagina web.

Los tres puntos con flecha deben ser:
1. Que no tiene web y sus competidores si — cada dia pierde pacientes que buscan en Google y encuentran a la competencia
2. Su ficha de Google Business: tiene {resenas} resenas con un {rating} — como se compara con la competencia en {ciudad}
3. Si alguien pregunta a ChatGPT por {sector_label} en {ciudad}, este negocio no aparece — los que si aparecen estan captando clientes sin hacer nada

NO incluyas enlace a informe ni CTA de "Ver mi analisis".
CTA principal: "Quieres que te expliquemos como empezar? Escribenos por WhatsApp."
"""

    prompt = f"""Eres Jesica, de N&G LAB Digital. Escribe un email frio B2B para {nombre} ({ciudad}).
Sector: {nicho}.

{contexto}

ESTRUCTURA OBLIGATORIA del email:
1. Saludo "Hola," (tuteo siempre)
2. Presentacion: "Soy Jesica, de N&G LAB Digital. Llevamos semanas analizando la visibilidad online de {sector_label} en {ciudad} — no todas, solo las que consideramos que tienen potencial real para crecer digitalmente."
3. Frase: "{nombre} es uno de ellos." o "una de ellas." segun el nombre
4. "Hemos preparado un analisis gratuito con tres datos que probablemente no conoces sobre tu presencia digital:"
5. Tres puntos con flecha (→) redactados de forma que generen curiosidad sin ser agresivos
6. Cierre segun el caso (con o sin web)
7. "Quieres que te expliquemos los resultados? Escribenos por WhatsApp y te atendemos en menos de 24 horas."
8. Firma: "Un saludo, Jesica Marquez — N&G LAB Digital — nglabdigital.com"

REGLAS:
- Maximo 180 palabras el cuerpo
- Tuteo siempre, nunca usted
- Tono cercano pero profesional, sin adulaciones falsas
- No uses acentos en el JSON (escribir "analisis" no "análisis")
- El asunto debe ser corto y generar curiosidad, maximo 8 palabras

Responde UNICAMENTE con un objeto JSON valido, sin markdown, sin acentos invertidos. Formato exacto:
{{"asunto": "texto del asunto", "cuerpo_texto": "version texto plano", "cuerpo_html": "<p>version HTML con <br> para saltos de linea</p>"}}

IMPORTANTE: No uses saltos de linea dentro de los valores del JSON. Usa <br> en el HTML. Responde SOLO el JSON."""

    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": MODELO, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = httpx.post(URL, headers=headers, json=body, timeout=60)
        t = r.json()["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
        return json.loads(t)
    except Exception as e:
        print(f"Error: {e}")
        return None

def main(nicho=None):
    leads = leads_por_estado("informe_generado", nicho=nicho) or leads_por_estado("auditado", nicho=nicho)
    print(f"[EMAIL] {len(leads)} leads")
    for lead in leads:
        lid = lead.get("id")
        nombre = lead.get("nombre_negocio", "")
        n = nicho or lead.get("sector", "general")
        r = generar(lead, n)
        if r:
            actualizar_lead(lid, email_asunto=r.get("asunto"), email_cuerpo=r.get("cuerpo_texto"), email_html=r.get("cuerpo_html"), estado="listo_para_enviar")
            print(f"  OK {nombre}")
        else:
            print(f"  ERROR {nombre}")
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
