from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
import httpx

def ahora():
    return datetime.now(timezone.utc).isoformat()

def _h():
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _url(t):
    return os.getenv("SUPABASE_URL", "").rstrip("/") + f"/rest/v1/{t}"

# ─── Rotación de municipios (ahora en Supabase, no SQLite) ───────────────────

def init_db():
    """Compatibilidad — ya no hace nada, la tabla existe en Supabase."""
    pass

def registrar_prospeccion(nicho: str, municipio: str):
    with httpx.Client(timeout=15) as c:
        c.post(
            _url("motor_prospeccion_log"),
            json={"nicho": nicho, "municipio": municipio, "fecha": ahora()},
            headers={**_h(), "Prefer": "return=minimal,resolution=ignore-duplicates"},
        )

registrar_busqueda = registrar_prospeccion

def busquedas_hechas() -> set:
    with httpx.Client(timeout=15) as c:
        r = c.get(
            _url("motor_prospeccion_log") + "?select=nicho,municipio&limit=10000",
            headers=_h(),
        )
        if r.status_code == 200:
            return {(row["nicho"], row["municipio"]) for row in r.json()}
    return set()

# ─── Leads ───────────────────────────────────────────────────────────────────

def upsert_lead(datos):
    payload = {
        "org_id": os.getenv("ORG_ID", ""),
        "nombre_negocio": datos.get("nombre", ""),
        "ciudad": datos.get("municipio", ""),
        "provincia": datos.get("provincia", ""),
        "telefono": datos.get("telefono", ""),
        "web": datos.get("web", ""),
        "sector": datos.get("nicho", ""),
        "estado": "nuevo",
        "fuente": "google_places",
        "calificacion_google": datos.get("rating"),
        "resenas_google": datos.get("num_resenas"),
        "token_baja": str(uuid.uuid4()),
        "created_at": ahora(),
        "updated_at": ahora(),
    }
    with httpx.Client(timeout=15) as c:
        r = c.post(_url("crm_leads"), json=payload, headers=_h())
        if r.status_code not in (200, 201):
            print(f"  ERROR upsert {r.status_code} {r.text[:100]}")

def leads_por_estado(estado, con_web=False, nicho=None):
    org_id = os.getenv("ORG_ID", "")
    query = f"?org_id=eq.{org_id}&estado=eq.{estado}&select=*"
    if con_web:
        query += "&web=not.is.null&web=neq."
    if nicho:
        query += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + query, headers=_h())
        if r.status_code == 200:
            return r.json()
        print(f"  ERROR leads_por_estado {r.status_code}: {r.text[:100]}")
        return []

def actualizar_lead(lead_id, **campos):
    campos["updated_at"] = ahora()
    with httpx.Client(timeout=30) as c:
        r = c.patch(
            _url("crm_leads") + f"?id=eq.{lead_id}",
            json=campos,
            headers=_h(),
        )
        if r.status_code not in (200, 204):
            print(f"  PATCH ERROR {r.status_code}: {r.text[:200]}")
            return False
    return True

def lote_para_envio(limite):
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(
            _url("crm_leads") +
            f"?org_id=eq.{org_id}"
            f"&estado=eq.listo_para_enviar"
            f"&email=not.is.null"
            f"&dado_de_baja=eq.false"
            f"&select=*"
            f"&limit={limite}",
            headers=_h(),
        )
        return r.json() if r.status_code == 200 else []

def email_excluido(email: str) -> bool:
    if not email:
        return False
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=10) as c:
        r = c.get(
            _url("crm_leads") +
            f"?org_id=eq.{org_id}&email=eq.{email}&dado_de_baja=eq.true&select=id&limit=1",
            headers=_h(),
        )
        if r.status_code == 200:
            return len(r.json()) > 0
    return False

def excluir_email(email: str, motivo: str = "baja_voluntaria") -> bool:
    if not email:
        return False
    org_id = os.getenv("ORG_ID", "")
    campos = {"dado_de_baja": True, "notas": f"Baja voluntaria: {motivo}", "updated_at": ahora()}
    with httpx.Client(timeout=10) as c:
        r = c.patch(
            _url("crm_leads") + f"?org_id=eq.{org_id}&email=eq.{email}",
            json=campos,
            headers=_h(),
        )
        if r.status_code in (200, 204):
            print(f"  [BAJA] {email} marcado como dado_de_baja ({motivo})")
            return True
        print(f"  [BAJA] ERROR {r.status_code}: {r.text[:100]}")
        return False

def stats(nicho=None):
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&select=estado"
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_h())
        filas = r.json() if r.status_code == 200 else []
    conteo = {"total": len(filas)}
    for f in filas:
        e = f.get("estado", "?")
        conteo[e] = conteo.get(e, 0) + 1
    return conteo

def stats_por_nicho():
    return {}

def cargar_json(texto):
    try:
        return json.loads(texto) if texto else None
    except Exception:
        return None
