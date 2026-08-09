from __future__ import annotations
import httpx
from config import GOOGLE_PLACES_API_KEY, NICHOS, nicho_config
from db import upsert_lead, registrar_busqueda, stats

URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.nationalPhoneNumber", "places.websiteUri",
    "places.rating", "places.userRatingCount", "places.businessStatus",
    "nextPageToken",
])
HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
    "X-Goog-FieldMask": FIELD_MASK,
}

def buscar(query: str) -> list[dict]:
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
    return resultados

def procesar_municipio(nicho: str, municipio: str, provincia: str):
    cfg = nicho_config(nicho)
    total = 0
    for tpl in cfg["queries"]:
        query = tpl.format(m=municipio, p=provincia)
        places = buscar(query)
        for p in places:
            estado = p.get("businessStatus", "")
            if estado and estado != "OPERATIONAL":
                continue
            web = p.get("websiteUri", "")
            telefono = p.get("nationalPhoneNumber", "")
            nombre = p.get("displayName", {}).get("text", "Sin nombre")
            upsert_lead({
                "place_id": p.get("id", ""),
                "nombre": nombre,
                "direccion": p.get("formattedAddress", ""),
                "municipio": municipio,
                "provincia": provincia,
                "telefono": telefono,
                "web": web,
                "nicho": nicho,
                "rating": p.get("rating"),
                "num_resenas": p.get("userRatingCount"),
            })
            total += 1
    print(f"  {municipio}: {total} negocios encontrados")
