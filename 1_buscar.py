from __future__ import annotations
"""NGLAB Motor — Paso 1: Buscar negocios en Google Maps (Places API New).

Uso:
    python3 1_buscar.py dental Valencia     # un nicho, un municipio
    python3 1_buscar.py dental              # un nicho, todos los municipios
    python3 1_buscar.py lista              # ver nichos disponibles
"""
import sys
import time

import httpx

from config import GOOGLE_PLACES_API_KEY, MUNICIPIOS, NICHOS, nicho_config
from db import upsert_lead, registrar_busqueda, stats

URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "nextPageToken",
])

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
    "X-Goog-FieldMask": FIELD_MASK,
}


def buscar(query: str) -> list[dict]:
    """Búsqueda paginada (máx. 3 páginas = 60 resultados)."""
    resultados, page_token = [], None
    with httpx.Client(timeout=30) as cliente:
        for _ in range(3):
            body: dict = {"textQuery": query, "languageCode": "es"}
            if page_token:
                body["pageToken"] = page_token
            r = cliente.post(URL, headers=HEADERS, json=body)
            if r.status_code != 200:
                print(f"  [ERROR {r.status_code}] {r.text[:200]}")
                break
            data = r.json()
            resultados.extend(data.get("places", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            time.sleep(2)
    return resultados


def procesar_municipio(nicho: str, municipio: str, provincia: str) -> int:
    cfg = nicho_config(nicho)
    nuevos = 0
    for plantilla in cfg["queries"]:
        query = plantilla.format(m=municipio, p=provincia)
        for p in buscar(query):
            if p.get("businessStatus") == "CLOSED_PERMANENTLY":
                continue
            web = p.get("websiteUri")
            telefono = p.get("nationalPhoneNumber")
            # Sin web ni teléfono no podemos contactar
            if not web and not telefono:
                continue
            resultado = upsert_lead({
                "place_id": p["id"],
                "nombre": p.get("displayName", {}).get("text", "Sin nombre"),
                "direccion": p.get("formattedAddress"),
                "municipio": municipio,
                "provincia": provincia,
                "telefono": telefono,
                "web": web,
                "rating": p.get("rating"),
                "num_resenas": p.get("userRatingCount"),
                "nicho": nicho,
            })
            if resultado:
                nuevos += 1
        time.sleep(0.5)

    registrar_busqueda(nicho, municipio)
    return nuevos


def listar_nichos():
    print("Nichos disponibles:\n")
    for clave, cfg in NICHOS.items():
        print(f"  {clave:15} {cfg['nombre']}")
    print("\nUso: python3 1_buscar.py <nicho> [municipio]")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "lista":
        listar_nichos()
        return
    if not GOOGLE_PLACES_API_KEY:
        sys.exit("Falta GOOGLE_PLACES_API_KEY en .env")

    nicho = sys.argv[1].lower()
    nicho_config(nicho)  # valida que existe

    filtro = sys.argv[2].lower() if len(sys.argv) > 2 else None
    objetivos = [(m, p) for m, p in MUNICIPIOS
                 if not filtro or m.lower() == filtro]
    if not objetivos:
        sys.exit(f"Municipio '{sys.argv[2]}' no está en la lista de config.py")

    print(f"Nicho: {NICHOS[nicho]['nombre']} · Localidades: {len(objetivos)}\n")
    for i, (municipio, provincia) in enumerate(objetivos, 1):
        print(f"[{i}/{len(objetivos)}] {municipio} ({provincia})...")
        n = procesar_municipio(nicho, municipio, provincia)
        print(f"  -> {n} leads nuevos guardados")

    print("\nResumen global:", stats())


if __name__ == "__main__":
    main()
