from __future__ import annotations
"""NGLAB Motor - Orquestador de prospeccion.
Logica identica a KD-Radar pero con Supabase para leads y SQLite para rotacion.
"""
import importlib
import threading
import traceback

from config import ANTHROPIC_API_KEY, MUNICIPIOS, NICHOS
from db import init_db, registrar_prospeccion, busquedas_hechas, stats

_lock = threading.Lock()
estado_motor: dict = {"ocupado": False, "ultima_ejecucion": None, "error": None}


def siguientes_combos(cuantos: int) -> list[tuple[str, str, str]]:
    """Rotacion round-robin identica a KD-Radar.
    Elige el nicho con menos municipios completados.
    Nunca repite un combo ya prospectado.
    """
    hechas = busquedas_hechas()
    conteo = {n: 0 for n in NICHOS}
    for n, _m in hechas:
        if n in conteo:
            conteo[n] += 1
    total_municipios = len(MUNICIPIOS)
    candidatos = [n for n in NICHOS if conteo[n] < total_municipios]
    if not candidatos:
        return []
    orden = list(NICHOS)
    candidatos.sort(key=lambda n: (conteo[n], orden.index(n)))
    nicho = candidatos[0]
    pendientes = [(nicho, m, p) for m, p in MUNICIPIOS if (nicho, m) not in hechas]
    return pendientes[:cuantos]


def ejecutar_pipeline(municipios_por_dia: int = 3) -> dict:
    """Ejecuta el pipeline completo para los proximos municipios."""
    if not _lock.acquire(blocking=False):
        return {"ok": False, "motivo": "Ya hay una prospeccion en curso"}
    estado_motor.update(ocupado=True, error=None)
    try:
        init_db()
        combos = siguientes_combos(municipios_por_dia)
        if not combos:
            return {"ok": True, "mensaje": "Todos los nichos y municipios prospectados."}

        nicho = combos[0][0]
        procesados = []

        # 1. Buscar negocios en Google Maps
        mod_buscar = importlib.import_module("1_buscar")
        for n, municipio, provincia in combos:
            print(f"[MOTOR] 1/5 Buscando {n} en {municipio}...")
            mod_buscar.procesar_municipio(n, municipio, provincia)
            registrar_prospeccion(n, municipio)
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

        # 5. Generar emails con Claude
        if ANTHROPIC_API_KEY:
            print("[MOTOR] 5/5 Generando emails con Claude...")
            try:
                importlib.import_module("4_generar_emails").main(nicho=nicho)
            except Exception as e:
                print(f"[MOTOR] Generacion de emails fallo ({type(e).__name__}: {e}); pipeline completo igualmente")
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
