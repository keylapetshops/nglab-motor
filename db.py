from __future__ import annotations
"""NGLAB Motor - Capa de datos.
SQLite local para rotacion de municipios (igual que KD-Radar).
Supabase para leads (crm_leads).
"""
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import httpx

DB_PATH = os.getenv("DB_PATH", "nglab_motor.db")

# ---------------------------------------------------------------------------
# SQLite local - solo para rotacion de municipios
# ---------------------------------------------------------------------------
SCHEMA_LOCAL = """
CREATE TABLE IF NOT EXISTS prospeccion_log (
    nicho TEXT,
    municipio TEXT,
    fecha TEXT,
    PRIMARY KEY (nicho, municipio)
);
"""

def ahora() -> str:
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

# Alias publico para compatibilidad con servidor.py
conexion = _conexion

def init_db():
    with _conexion() as con:
        con.executescript(SCHEMA_LOCAL)

def registrar_prospeccion(nicho: str, municipio: str):
    with _conexion() as con:
        con.execute(
            "INSERT OR IGNORE INTO prospeccion_log (nicho, municipio, fecha) VALUES (?,?,?)",
            (nicho, municipio, ahora()),
        )

def busquedas_hechas() -> set[tuple[str, str]]:
    init_db()
    with _conexion() as con:
        return {(r["nicho"], r["municipio"]) for r in
                con.execute("SELECT nicho, municipio FROM prospeccion_log")}

# ---------------------------------------------------------------------------
# Supabase - para leads
# ---------------------------------------------------------------------------
def _headers():
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _url(tabla: str) -> str:
    base = os.getenv("SUPABASE_URL", "").rstrip("/")
    return f"{base}/rest/v1/{tabla}"

def upsert_lead(datos: dict):
    org_id = os.getenv("ORG_ID", "")
    payload = {
        "org_id": org_id,
        "nombre_negocio": datos.get("nombre"),
        "direccion": datos.get("direccion"),
        "ciudad": datos.get("municipio"),
        "provincia": datos.get("provincia"),
        "telefono": datos.get("telefono"),
        "website": datos.get("web"),
        "sector": datos.get("nicho", ""),
        "estado": "nuevo",
        "fuente": "google_places",
        "google_place_id": datos.get("place_id"),
        "rating": datos.get("rating"),
        "num_resenas": datos.get("num_resenas"),
        "token_baja": secrets.token_urlsafe(16),
        "created_at": ahora(),
        "updated_at": ahora(),
    }
    with httpx.Client(timeout=15) as c:
        c.post(
            _url("crm_leads") + "?on_conflict=google_place_id",
            json=payload,
            headers={**_headers(), "Prefer": "resolution=ignore-duplicates,return=representation"},
        )

def leads_por_estado(estado: str, nicho: str | None = None) -> list[dict]:
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&estado=eq.{estado}&select=*"
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_headers())
        return r.json() if r.status_code == 200 else []

def actualizar_lead(lead_id: str, **campos):
    campos["updated_at"] = ahora()
    with httpx.Client(timeout=15) as c:
        c.patch(
            _url("crm_leads") + f"?id=eq.{lead_id}",
            json=campos,
            headers=_headers(),
        )

def lote_para_envio(limite: int) -> list[dict]:
    """Leads redactados con email valido listos para enviar."""
    org_id = os.getenv("ORG_ID", "")
    params = (f"?org_id=eq.{org_id}&estado=eq.redactado"
              f"&email=not.is.null&select=*&limit={limite}&order=created_at.asc")
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_headers())
        return r.json() if r.status_code == 200 else []

def email_excluido(email: str) -> bool:
    if not email:
        return True
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(
            _url("crm_leads") + f"?org_id=eq.{org_id}&email=eq.{email}&baja=eq.true&select=id",
            headers=_headers(),
        )
        return bool(r.json()) if r.status_code == 200 else False

def excluir_email(email: str, motivo: str = "baja_voluntaria"):
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        c.patch(
            _url("crm_leads") + f"?org_id=eq.{org_id}&email=eq.{email}",
            json={"baja": True, "estado": "descartado", "updated_at": ahora()},
            headers=_headers(),
        )

def stats(nicho: str | None = None) -> dict:
    org_id = os.getenv("ORG_ID", "")
    params = f"?org_id=eq.{org_id}&select=estado"
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + params, headers=_headers())
        filas = r.json() if r.status_code == 200 else []
    conteo: dict = {"total": len(filas)}
    for f in filas:
        e = f.get("estado", "desconocido")
        conteo[e] = conteo.get(e, 0) + 1
    return conteo

def stats_por_nicho() -> dict:
    org_id = os.getenv("ORG_ID", "")
    with httpx.Client(timeout=15) as c:
        r = c.get(_url("crm_leads") + f"?org_id=eq.{org_id}&select=sector", headers=_headers())
        filas = r.json() if r.status_code == 200 else []
    conteo: dict = {}
    for f in filas:
        s = f.get("sector", "desconocido")
        conteo[s] = conteo.get(s, 0) + 1
    return conteo

def cargar_json(texto: str | None):
    try:
        return json.loads(texto) if texto else None
    except json.JSONDecodeError:
        return None
