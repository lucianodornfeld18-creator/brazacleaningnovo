# -*- coding: utf-8 -*-
"""Sincroniza reviews REAIS do Google Business Profile via Places API (New).

POR QUE: estrelas no schema do proprio negocio sao "self-serving" (Google ignora/pune).
A estrategia certa: exibir reviews reais VISIVEIS no HTML (texto/autor/data), sem schema.

REQUISITOS (Luciano fornece, uma vez):
  - env GOOGLE_PLACES_API_KEY : chave com Places API (New) habilitada (console.cloud.google.com)
  - env BRAZA_PLACE_ID        : Place ID do perfil (developers.google.com/maps/documentation/places/web-service/place-id)

Uso: python automation/fetch_reviews.py
Salva automation/reviews_live.json (exemplo sintetico):
  {"rating": 5.0, "count": 0, "fetched": "2026-01-01",
   "reviews": [{"author": "Nome", "rating": 5, "date": "2026-01-01", "text": "..."}]}
A injecao no HTML (secao de reviews visivel) e o passo seguinte do plano (W6).
"""
import json, os, sys, datetime, urllib.request

KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
PLACE_ID = os.environ.get("BRAZA_PLACE_ID")
OUT = os.path.join(os.path.dirname(__file__), "reviews_live.json")

def main():
    if not KEY or not PLACE_ID:
        sys.exit("Defina GOOGLE_PLACES_API_KEY e BRAZA_PLACE_ID. Veja docstring para o passo a passo.")
    url = f"https://places.googleapis.com/v1/places/{PLACE_ID}"
    req = urllib.request.Request(url, headers={
        "X-Goog-Api-Key": KEY,
        "X-Goog-FieldMask": "rating,userRatingCount,reviews",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = {
        "rating": data.get("rating"),
        "count": data.get("userRatingCount"),
        "fetched": datetime.date.today().isoformat(),
        "reviews": [
            {
                "author": rv.get("authorAttribution", {}).get("displayName"),
                "rating": rv.get("rating"),
                "date": rv.get("publishTime", "")[:10],
                "text": rv.get("text", {}).get("text", ""),
            }
            for rv in data.get("reviews", [])
        ],
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("rating=%s count=%s reviews=%d -> %s" % (out["rating"], out["count"], len(out["reviews"]), OUT))

if __name__ == "__main__":
    main()
