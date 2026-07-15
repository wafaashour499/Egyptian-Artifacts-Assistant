import requests
import json
import time
from collections import defaultdict

WIKIDATA_URL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "EgyptianMuseumRAG/1.0"}

def fetch_artifacts():
    query = """
    SELECT ?item ?itemLabel ?itemDescription ?image ?material ?materialLabel ?inception WHERE {
      ?item wdt:P195 wd:Q201219 .
      OPTIONAL { ?item wdt:P18 ?image . }
      OPTIONAL { ?item wdt:P186 ?material . }
      OPTIONAL { ?item wdt:P571 ?inception . }
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ar,en".
      }
    }
    """
    r = requests.get(
        WIKIDATA_URL,
        params={"query": query, "format": "json"},
        headers=HEADERS,
        timeout=30
    )
    return r.json()["results"]["bindings"]

def parse_result(r):
    return {
        "item_id": r["item"]["value"].split("/")[-1],
        "label": r["itemLabel"]["value"],
        "description": r.get("itemDescription", {}).get("value"),
        "image": r.get("image", {}).get("value"),
        "material": r.get("materialLabel", {}).get("value"),
        "inception": r.get("inception", {}).get("value"),
    }

def merge_artifacts(results):
    merged = defaultdict(lambda: {
        "item_id": None,
        "label": None,
        "description": None,
        "image": None,
        "materials": set(),
        "inception": None,
    })

    for r in results:
        item = parse_result(r)
        key = item["item_id"]
        merged[key]["item_id"] = item["item_id"]
        merged[key]["label"] = item["label"]
        merged[key]["description"] = item.get("description")
        merged[key]["image"] = item.get("image")
        merged[key]["inception"] = item.get("inception")
        if item.get("material"):
            merged[key]["materials"].add(item["material"])

    data = list(merged.values())
    for item in data:
        item["materials"] = list(item["materials"])

    return [x for x in data if x["image"] and x["label"] != x["item_id"]]

def build_document_text(item):
    parts = [f"Title: {item['label']}"]
    if item.get("description"):
        parts.append(f"Description: {item['description']}")
    if item.get("materials"):
        parts.append(f"Material: {', '.join(item['materials'])}")
    if item.get("inception"):
        parts.append(f"Date: {item['inception']}")
    parts.append("Museum: Egyptian Museum, Cairo")
    return "\n".join(parts)

def load_and_save(path="data/egyptian_museum_cairo.json"):
    results = fetch_artifacts()
    artifacts = merge_artifacts(results)
    for item in artifacts:
        item["document_text"] = build_document_text(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, ensure_ascii=False, indent=2)
    print(f"تم حفظ {len(artifacts)} قطعة")
    return artifacts