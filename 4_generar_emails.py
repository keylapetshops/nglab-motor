from __future__ import annotations
import json, sys, time, httpx
from config import ANTHROPIC_API_KEY, INFORMES_BASE, nicho_config
from db import leads_por_estado, actualizar_lead, cargar_json

MODELO = "claude-sonnet-4-5"
URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """Eres el copywriter senior de N&G LAB Digital, una agencia de marketing y tecnologia en Valencia. Escribes emails frios B2B que suenan como si una persona real hubiera dedicado tiempo a estudiar ese negocio concreto.

TU PERSONALIDAD AL ESCRIBIR:
- Hablas como Jesica, la fundadora: cercana, directa, segura, sin arrogancia
- Tuteas siempre, pero con respeto profesional
- Nunca usas palabras tecnicas que el dueno de un negocio local no entienda
- No adulas. No dices "excelente negocio" ni "gran trabajo". Si algo es bueno, lo dices con datos concretos
- Cada frase tiene un proposito. Si no aporta, la quitas
- Generas curiosidad sin ser agresiva. Muestras el problema sin asustar

REGLAS DE CALIDAD:
- Usa los datos REALES del lead: puntuacion exacta, numero de resenas, rating, ciudad, nombre del negocio
- Los pain points no son genericos: son especificos de lo que has encontrado en SU negocio
- El asunto del email debe tener maximo 7 palabras y mencionar el nombre del negocio
- No repitas la misma estructura en todos los emails: varia la entrada, el enfoque, el cierre
- Escribe como si fuera UN email para UNA persona, no una plantilla para 200"""

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
        caso = f"""DATOS DEL NEGOCIO:
- Nombre: {nombre}
- Ciudad: {ciudad}
- Sector: {nicho}
- Web: {web}
- PageSpeed movil: {ps}/100
- Rating Google: {rating}
- Resenas Google: {resenas}
- Pain point 1: {dolor1}
- Pain point 2: {dolor2}
- Pain point 3: {dolor3}
- URL del informe: {url}

TIPO: CON WEB
Escribe el email usando los pain points reales de su web. Incluye el boton "Ver el analisis de mi negocio" con el enlace al informe. Cierra con opcion de WhatsApp."""
    else:
        caso = f"""DATOS DEL NEGOCIO:
- Nombre: {nombre}
- Ciudad: {ciudad}
- Sector: {nicho}
- Web: NO TIENE
- Rating Google: {rating}
- Resenas Google: {resenas}

TIPO: SIN WEB
Este negocio no tiene pagina web. Los tres puntos deben girar en torno a:
1. No tener web cuando su competencia si la tiene — que esta perdiendo
2. Su perfil de Google Business: {resenas} resenas con un {rating} — como se compara
3. Si alguien pregunta a una IA por {sector_label} en {ciudad}, no aparece

NO incluyas enlace a informe. El CTA principal es WhatsApp."""

    prompt = f"""{caso}

ESTRUCTURA DEL EMAIL:
1. "Hola," (siempre)
2. Presentacion corta de Jesica y N&G LAB — por que les escribes, que has hecho (NO uses la frase "llevamos semanas analizando" en todos, varia)
3. Una frase destacada con el nombre del negocio
4. "He mirado vuestro caso y hay tres cosas que creo que os interesa saber:" (o variacion natural)
5. Tres puntos con flecha (→) usando los datos REALES — que suenen a que alguien ha dedicado tiempo a mirar SU caso, no una plantilla
6. Cierre con CTA segun el tipo (con o sin web)
7. Opcion de WhatsApp
8. Firma: Jesica Marquez / N&G LAB Digital / nglabdigital.com

FORMATO DE RESPUESTA — JSON puro, sin markdown:
{{"asunto": "maximo 7 palabras con nombre del negocio", "cuerpo_texto": "version texto plano del email", "cuerpo_html": "version HTML del email usando <br> para saltos de linea, <strong> para negritas, <p> para parrafos"}}

El cuerpo_html debe incluir las flechas → para los puntos. No uses saltos de linea reales dentro de los valores JSON. Maximo 200 palabras el cuerpo. Responde SOLO el JSON."""

    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": MODELO, "max_tokens": 2000, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]}
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
