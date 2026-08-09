from __future__ import annotations
import json, os, secrets, sqlite3
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

def _headers():
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=representation"}

def _url(tabla):
    return os.getenv("SUPABASE_URL", "").rstrip("/") + f"/rest/v1/{tabla}"

def upsert_lead(datos):
    org_id = os.getenv("ORG_ID", "")
    nombre = datos.get("nombre", "")
    ciudad = datos.get("municipio", "")
    with httpx.Client(timeout=15) as c:
        check = c.get(_url("crm_leads") + f"?org_id=eq.{org_id}&nombre_negocio=eq.{nombre}&ciudad=eq.{ciudad}&select=id", headers=_headers())
        if check.status_code == 200 and check.json():
            return
        payload = {"org_id": org_id, "nombre_negocio": nombre, "direccion": datos.get("direccion"), "ciudad": ciudad, "provincia": datos.get("provincia"), "telefono": datos.get("telefono"), "web": datos.get("web"), "sector": datos.get("nicho", ""), "estado": "nuevo", "fuente": "google_places", "calificacion_google": datos.get("rating"), "resenas_google": datos.get("num_resenas"), "token_baja": secrets.token_urlsafe(16), "created_at": ahora(), "updated_at": ahora()}
        c.post(_url("crm_leads"), json=payload, headers=_headers())

def leads_por_estado(estado, con_web=False, nicho=None):
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&estado=eq.{estado}&select=*"
    if con_web:
        params += "&web=not.is.null"
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_headers())
        return r.json() if r.status_code == 200 else []

def actualizar_lead(lead_id, **campos):
    campos["updated_at"] = ahora()
    with httpx.Client(timeout=15) as c:
        c.patch(_url("crm_leads") + f"?id=eq.{lead_id}", json=campos, headers=_headers())

def lote_para_envio(limite):
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + f"?org_id=eq.{org_id}&estado=eq.redactado&email=not.is.null&select=*&limit={limite}&order=created_at.asc", headers=_headers())
        return r.json() if r.status_code == 200 else []

def email_excluido(email):
    if not email:
        return True
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + f"?org_id=eq.{org_id}&email=eq.{email}&dado_de_baja=eq.true&select=id", headers=_headers())
        return bool(r.json()) if r.status_code == 200 else False

def excluir_email(email, motivo="baja_voluntaria"):
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        c.patch(_url("crm_leads") + f"?org_id=eq.{org_id}&email=eq.{email}", json={"dado_de_baja": True, "estado": "descartado", "updated_at": ahora()}, headers=_headers())

def stats(nicho=None):
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&select=estado"
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_headers())
        filas = r.json() if r.status_code == 200 else []
    conteo = {"total": len(filas)}
    for f in filas:
        e = f.get("estado", "desconocido")
        conteo[e] = conteo.get(e, 0) + 1
    return conteo

def stats_por_nicho():
    return {}

def cargar_json(texto):
    try:
        return json.loads(texto) if texto else None
    except:
        return None
