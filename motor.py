from __future__ import annotations
"""NGLAB Motor — Orquestador del pipeline completo.

Pipeline por ejecución:
  1. Buscar negocios (Google Places)
  2. Extraer emails + separar sin_web / sin_email
  3. Validar emails (sintaxis + MX DNS)
  4. Auditar web + PageSpeed
  5. Generar emails con Claude (SOLO leads con email válido)

Rotación automática: nicho con menos municipios completados → round-robin.
Nunca repite un combo (nicho, municipio) ya prospectado.
"""
import importlib
import threading
import traceback

from config import MUNICIPIOS, NICHOS, ANTHROPIC_API_KEY
from db import busquedas_hechas, stats

_lock = threading.Lock()

estado_motor: dict = {
    "ocupado": False,
    "ultima_ejecucion": None,
    "error": None,
}


def siguientes_combos(cuantos: int) -> list[tuple[str, str, str]]:
    """Devuelve los próximos combos (nicho, municipio, provincia) pendientes."""
    hechas = busquedas_hechas()
    total_municipios = len(MUNICIPIOS)

    conteo = {n: 0 for n in NICHOS}
    for nicho, municipio in hechas:
        if nicho in conteo:
            conteo[nicho] += 1

    candidatos = [n for n in NICHOS if conteo[n] < total_municipios]
    if not candidatos:
        return []

    orden = list(NICHOS)
    candidatos.sort(key=lambda n: (conteo[n], orden.index(n)))
    nicho = candidatos[0]

    pendientes = [
        (nicho, m, p) for m, p in MUNICIPIOS
        if (nicho, m) not in hechas
    ]
    return pendientes[:cuantos]


def ejecutar_pipeline(municipios_por_dia: int = 3) -> dict:
    """Ejecuta el pipeline completo para los próximos municipios."""
    if not _lock.acquire(blocking=False):
        return {"ok": False, "motivo": "Ya hay una prospección en curso"}

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

        # 2. Extraer emails (separa sin_web / sin_email / con_email)
        print("[MOTOR] 2/5 Extrayendo emails...")
        importlib.import_module("2_extraer_emails").main()

        # 3. Validar emails (MX DNS) — elimina emails inválidos antes de auditar
        print("[MOTOR] 3/5 Validando emails (MX)...")
        importlib.import_module("5_validar_emails").main()

        # 4. Auditar web + PageSpeed
        print("[MOTOR] 4/5 Auditando webs + PageSpeed...")
        importlib.import_module("3_auditar").main(nicho=nicho)

        # 5. Generar emails con Claude (SOLO leads con email válido)
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
