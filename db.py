from __future__ import annotations
import json, os, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
import httpx

DB_PATH = os.getenv("DB_PATH", "nglab_motor.db")

def ahora():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def _conexion():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

conexion = _conexion

def init_db():
    with _conexion() as con:
        con.executescript("CREATE TABLE IF NOT EXISTS prospeccion_log (nicho TEXT, municipio TEXT, fecha TEXT, PRIMARY KEY (nicho, municipio));")

def registrar_prospeccion(nicho, municipio):
    with _conexion() as con:
        con.execute("INSERT OR IGNORE INTO prospeccion_log (nicho, municipio, fecha) VALUES (?,?,?)", (nicho, municipio, ahora()))

registrar_busqueda = registrar_prospeccion

def busquedas_hechas():
    init_db()
    with _conexion() as con:
        return {(r["nicho"], r["municipio"]) for r in con.execute("SELECT nicho, municipio FROM prospeccion_log")}

def _h():
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

def _url(t):
    return os.getenv("SUPABASE_URL", "").rstrip("/") + f"/rest/v1/{t}"

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
            print(f"  ERROR {r.status_code} {r.text[:100]}")

def leads_por_estado(estado, con_web=False, nicho=None):
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&estado=eq.{estado}&select=*"
    if con_web:
        params += "&web=not.is.null&web=neq."
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_h())
        return r.json() if r.status_code == 200 else []

def actualizar_lead(lead_id, **campos):
    campos["updated_at"] = ahora()
    with httpx.Client(timeout=15) as c:
        c.patch(_url("crm_leads") + f"?id=eq.{lead_id}", json=campos, headers=_h())

def lote_para_envio(limite):
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + f"?org_id=eq.{org_id}&estado=eq.redactado&email=not.is.null&select=*&limit={limite}", headers=_h())
        return r.json() if r.status_code == 200 else []

def email_excluido(email):
    return False

def excluir_email(email, motivo="baja_voluntaria"):
    pass

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
    except:
        return None
