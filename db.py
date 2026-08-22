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
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

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
        r = c.post(
            _url("crm_leads"),
            json=payload,
            headers=_h(),
        )
        if r.status_code not in (200, 201):
            print(f"  ERROR upsert {r.status_code} {r.text[:100]}")

def leads_por_estado(estado, con_web=False, nicho=None):
    """
    FIX: con_web=True ahora usa filtro correcto con dos condiciones separadas
    en vez de 'web=neq.' sin valor que rompía la query.
    """
    org_id = os.getenv("ORG_ID", "")
    params = {
        "org_id": f"eq.{org_id}",
        "estado": f"eq.{estado}",
        "select": "*",
    }
    if con_web:
        # Filtra leads que tienen web: no es null Y no es cadena vacía
        params["web"] = "not.is.null"
        params["web"] = "neq."  # esto se sobreescribe — usamos approach correcto abajo

    if nicho:
        params["sector"] = f"eq.{nicho}"

    # Build URL manualmente para manejar el doble filtro de web correctamente
    base = _url("crm_leads")
    query = f"?org_id=eq.{org_id}&estado=eq.{estado}&select=*"
    if con_web:
        query += "&web=not.is.null&web=neq.%22%22"
    if nicho:
        query += f"&sector=eq.{nicho}"

    with httpx.Client(timeout=15) as c:
        r = c.get(base + query, headers=_h())
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
    """
    FIX: estado corregido de 'redactado' (inexistente) a 'listo_para_enviar'.
    Antes esta función siempre devolvía [] porque el estado no existía.
    """
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
    """
    Comprueba si un email está marcado como dado_de_baja en Supabase.
    """
    if not email:
        return False
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=10) as c:
        r = c.get(
            _url("crm_leads") +
            f"?org_id=eq.{org_id}"
            f"&email=eq.{email}"
            f"&dado_de_baja=eq.true"
            f"&select=id"
            f"&limit=1",
            headers=_h(),
        )
        if r.status_code == 200:
            return len(r.json()) > 0
    return False

def excluir_email(email: str, motivo: str = "baja_voluntaria") -> bool:
    """
    FIX: antes era stub vacío — las bajas voluntarias no se procesaban.
    Ahora marca dado_de_baja=True en todos los leads con ese email.
    """
    if not email:
        return False
    org_id = os.getenv("ORG_ID", "")
    campos = {
        "dado_de_baja": True,
        "notas": f"Baja voluntaria: {motivo}",
        "updated_at": ahora(),
    }
    with httpx.Client(timeout=10) as c:
        r = c.patch(
            _url("crm_leads") +
            f"?org_id=eq.{org_id}"
            f"&email=eq.{email}",
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
