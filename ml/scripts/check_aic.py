import os
import requests

URL = "https://api.artic.edu/api/v1/artworks/search"
FIELDS = "id,title,artist_title,date_display,classification_title,is_public_domain,image_id"
HEADERS = {
    "User-Agent": "monet-canvas-research/0.1",
    "AIC-User-Agent": "monet-canvas (" + os.environ["AIC_CONTACT"] + ")",
}

found = []
for page in range(1, 6):
    r = requests.get(
        URL,
        params={
            "q": "Claude Monet",
            "query[term][is_public_domain]": "true",
            "fields": FIELDS,
            "limit": 100,
            "page": page,
        },
        headers=HEADERS,
        timeout=(15, 60),
    )
    r.raise_for_status()
    rows = r.json().get("data") or []
    if not rows:
        break
    for o in rows:
        if "Monet" in (o.get("artist_title") or "") and o.get("image_id"):
            found.append(o)

print("public-domain Monet works with an image:", len(found))
for o in found[:15]:
    print(" ", o["id"], "|", o["title"], "|", o["date_display"], "|", o["classification_title"])