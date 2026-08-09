# VERSION: 2.0 - usa crm_busquedas
"""
Motor de prospeccion NGLAB.
Pipeline por ejecucion:
  1. Buscar negocios (Google Places)
  2. Extraer emails + separar sin_web / sin_email
  3. Validar emails (sintaxis + MX DNS)
  4. Auditar web + PageSpeed
  5. Generar emails con Claude (SOLO leads con email valido)

Rotacion automatica: consulta crm_busquedas en Supabase.
Nunca repite un combo (nicho, municipio) ya prospectado.
"""
import importlib
import threading
import traceback
import os
import httpx

from config import NICHOS, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
from db import busquedas_hechas, stats

_lock = threading.Lock()

estado_motor: dict = {
    "ocupado": False,
    "ultima_ejecucion": None,
    "error": None,
}


def siguientes_combos(cuantos: int) -> list[tuple[str, str, str]]:
    """Devuelve los proximos combos (nicho, municipio, provincia) pendientes desde crm_busquedas."""
    hechas = busquedas_hechas()

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }

    # Obtener combos pendientes de crm_busquedas ordenados por prioridad
    url = (
        f"{SUPABASE_URL}/rest/v1/crm_busquedas"
        f"?select=nicho,ciudad,provincia&order=id.asc&limit=200"
    )
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get(url, headers=headers)
            filas = r.json() if r.status_code == 200 else []
    except Exception:
        filas = []

    pendientes = []
    for fila in filas:
        nicho = fila.get("nicho", "")
        ciudad = fila.get("ciudad", "")
        provincia = fila.get("provincia", "")
        if nicho in NICHOS and (nicho, ciudad) not in hechas:
            pendientes.append((nicho, ciudad, provincia))
        if len(pendientes) >= cuantos:
            break

    return pendientes


def ejecutar_pipeline(municipios_por_dia: int = 3) -> dict:
    """Ejecuta el pipeline completo para los proximos municipios."""
    if not _lock.acquire(blocking=False):
        return {"ok": False, "motivo": "Ya hay una prospeccion en curso"}

    estado_motor.update(ocupado=True, error=None)
    try:
        combos = siguientes_combos(municipios_por_dia)

        if not combos:
            return {
                "ok": True,
                "mensaje": "Todos los nichos y municipios prospectados.",
            }

        nicho = combos[0][0]
        procesados = []

        # 1. Buscar negocios en Google Maps
        mod = importlib.import_module("1_buscar")
        for n, municipio, provincia in combos:
            print(f"[MOTOR] 1/5 Buscando {n} en {municipio}...")
            mod.procesar_municipio(n, municipio, provincia)
            procesados.append(municipio)

        # 2. Extraer emails
        print("[MOTOR] 2/5 Extrayendo emails...")
        importlib.import_module("2_extraer_emails").main()

        # 3. Validar emails (MX DNS)
        print("[MOTOR] 3/5 Validando emails (MX)...")
        importlib.import_module("5_validar_emails").main()

        # 4. Auditar web + PageSpeed
        print("[MOTOR] 4/5 Auditando webs + PageSpeed...")
        importlib.import_module("3_auditar").main(nicho=nicho)

        # 5. Generar emails con Claude (solo leads con email valido)
        if ANTHROPIC_API_KEY:
            print("[MOTOR] 5/5 Generando emails con Claude...")
            importlib.import_module("4_generar_emails").main(nicho=nicho)
        else:
            print("[MOTOR] 5/5 SALTADO: falta ANTHROPIC_API_KEY")

        resumen = {
            "ok": True,
            "nicho": nicho,
            "nicho_nombre": NICHOS[nicho]["nombre"],
            "municipios": procesados,
            "stats": stats(),
        }
        estado_motor["ultima_ejecucion"] = resumen
        return resumen

    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        estado_motor["error"] = error
        traceback.print_exc()
        return {"ok": False, "motivo": error}
    finally:
        estado_motor["ocupado"] = False
        _lock.release()

