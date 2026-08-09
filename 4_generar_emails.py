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
    ps = int(lead.get("pagespeed_mobile", 0) or 0)
    dolores = cargar_json(lead.get("pain_points")) or []
    dolor = dolores[0] if dolores else cfg.get("dolor", "")
    url = lead.get("url_informe", f"{INFORMES_BASE}/{lead.get('id')}")
    prompt = f"Negocio: {nombre} ({ciudad}). PageSpeed: {ps}/100. Problema: {dolor}. URL informe: {url}. Escribe email frio B2B. Responde SOLO JSON: asunto, cuerpo_texto, cuerpo_html"
    headers = {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": MODELO, "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}
    try:
        r = httpx.post(URL, headers=headers, json=body, timeout=30)
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
