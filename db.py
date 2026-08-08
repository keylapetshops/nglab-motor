from __future__ import annotations
"""NGLAB Motor — Capa de datos (Supabase).

Trabaja contra la tabla crm_leads existente en Supabase.
No crea tablas nuevas — usa la estructura ya migrada.
"""
import json
import secrets
from datetime import datetime, timezone

import httpx

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, ORG_ID

# ---------------------------------------------------------------------------
# Cliente HTTP contra Supabase REST
# ---------------------------------------------------------------------------

def _headers() -> dict:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _url(tabla: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{tabla}"


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Operaciones sobre crm_leads
# ---------------------------------------------------------------------------

def upsert_lead(datos: dict) -> dict | None:
    """Inserta un lead nuevo. Si el nombre_negocio ya existe, no lo duplica."""
    payload = {
        "org_id": ORG_ID,
        "nombre_negocio": datos["nombre"],
        "ciudad": datos.get("municipio", ""),
        "provincia": datos.get("provincia", ""),
        "telefono": datos.get("telefono"),
        "web": datos.get("web"),
        "sector": datos.get("nicho", "otro"),
        "fuente": "google_maps",
        "estado": "nuevo",
        "calificacion_google": datos.get("rating"),
        "resenas_google": datos.get("num_resenas"),
        "token_baja": secrets.token_urlsafe(16),
        "created_at": ahora(),
        "updated_at": ahora(),
    }
    with httpx.Client(timeout=20) as c:
        r = c.post(
            _url("crm_leads") + "?on_conflict=nombre_negocio",
            headers={**_headers(), "Prefer": "resolution=ignore-duplicates,return=representation"},
            json=payload,
        )
    if r.status_code in (200, 201):
        data = r.json()
        return data[0] if data else None
    return None


def actualizar_lead(lead_id: str, **campos) -> bool:
    """Actualiza campos de un lead por su UUID."""
    campos["updated_at"] = ahora()
    with httpx.Client(timeout=20) as c:
        r = c.patch(
            _url("crm_leads") + f"?id=eq.{lead_id}",
            headers=_headers(),
            json=campos,
        )
    return r.status_code in (200, 204)


def leads_por_estado(estado: str, con_web: bool = False,
                     nicho: str | None = None) -> list[dict]:
    """Devuelve leads filtrados por estado."""
    params = f"estado=eq.{estado}&org_id=eq.{ORG_ID}"
    if con_web:
        params += "&web=not.is.null&web=neq."
    if nicho:
        params += f"&sector=eq.{nicho}"
    with httpx.Client(timeout=20) as c:
        r = c.get(
            _url("crm_leads") + f"?{params}",
            headers=_headers(),
        )
    if r.status_code == 200:
        return r.json()
    return []


def lote_para_envio(limite: int) -> list[dict]:
    """Leads auditados con email, listos para enviar."""
    params = (
        f"estado=eq.auditado&org_id=eq.{ORG_ID}"
        f"&email=not.is.null&email=neq."
        f"&dado_de_baja=eq.false"
        f"&email_invalido=eq.false"
        f"&pagespeed_fallido=eq.false"
        f"&order=created_at.asc&limit={limite}"
    )
    with httpx.Client(timeout=20) as c:
        r = c.get(_url("crm_leads") + f"?{params}", headers=_headers())
    return r.json() if r.status_code == 200 else []


def email_excluido(email: str) -> bool:
    """Comprueba si un email está en la lista de bajas."""
    with httpx.Client(timeout=10) as c:
        r = c.get(
            _url("crm_exclusiones") + f"?email=eq.{email.lower()}&org_id=eq.{ORG_ID}",
            headers=_headers(),
        )
    return bool(r.status_code == 200 and r.json())


def excluir_email(email: str, motivo: str = "baja_voluntaria") -> None:
    """Añade un email a la lista de exclusiones y marca el lead."""
    payload = {
        "email": email.lower(),
        "org_id": ORG_ID,
        "motivo": motivo,
        "fecha": ahora(),
    }
    with httpx.Client(timeout=10) as c:
        c.post(
            _url("crm_exclusiones") + "?on_conflict=email,org_id",
            headers={**_headers(), "Prefer": "resolution=ignore-duplicates,return=representation"},
            json=payload,
        )
        # Marcar lead como descartado
        c.patch(
            _url("crm_leads") + f"?email=eq.{email.lower()}&org_id=eq.{ORG_ID}",
            headers=_headers(),
            json={"estado": "descartado", "dado_de_baja": True,
                  "fecha_baja": ahora(), "updated_at": ahora()},
        )


def stats() -> dict:
    """Resumen del embudo de leads."""
    with httpx.Client(timeout=15) as c:
        r = c.get(
            _url("crm_leads") + f"?org_id=eq.{ORG_ID}&select=estado",
            headers=_headers(),
        )
    if r.status_code != 200:
        return {}
    leads = r.json()
    conteo: dict = {}
    for l in leads:
        estado = l.get("estado", "desconocido")
        conteo[estado] = conteo.get(estado, 0) + 1
    conteo["total"] = len(leads)
    return conteo


def cargar_json(texto: str | None):
    try:
        return json.loads(texto) if texto else None
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Registro de búsquedas realizadas (para no repetir combos)
# ---------------------------------------------------------------------------

def registrar_busqueda(nicho: str, municipio: str) -> None:
    payload = {
        "org_id": ORG_ID,
        "termino_busqueda": nicho,
        "ciudad": municipio,
        "sector": nicho,
        "plataforma": "google_maps",
        "estado": "usado",
        "ultima_ejecucion": ahora(),
        "created_at": ahora(),
        "updated_at": ahora(),
    }
    with httpx.Client(timeout=10) as c:
        c.post(
            _url("crm_busquedas") + "?on_conflict=termino_busqueda,ciudad,org_id",
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
            json=payload,
        )


def busquedas_hechas() -> set[tuple[str, str]]:
    """Devuelve los combos (nicho, municipio) ya prospectados."""
    with httpx.Client(timeout=15) as c:
        r = c.get(
            _url("crm_busquedas") + f"?org_id=eq.{ORG_ID}&estado=eq.usado&select=sector,ciudad",
            headers=_headers(),
        )
    if r.status_code != 200:
        return set()
    return {(row["sector"], row["ciudad"]) for row in r.json()}
