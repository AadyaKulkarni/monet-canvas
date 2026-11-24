import requests

URL = "https://openaccess-api.clevelandart.org/api/artworks/"
found = []

for skip in range(0, 300, 100):
    r = requests.get(
        URL,
        params={"q": "monet", "cc0": 1, "has_image": 1, "limit": 100, "skip": skip},
        headers={"User-Agent": "monet-canvas-research/0.1"},
        timeout=(15, 60),
    )
    print("status:", r.status_code)
    r.raise_for_status()
    rows = r.json().get("data") or []
    if not rows:
        break
    for a in rows:
        creators = " ".join(c.get("description", "") for c in (a.get("creators") or []))
        web = ((a.get("images") or {}).get("web") or {}).get("url")
        if "Claude Monet" in creators and web:
            found.append(a)

print("CC0 Monet works with an image:", len(found))
for a in found:
    print(" ", a["id"], "|", a.get("title"), "|", a.get("creation_date"), "|", a.get("type"), "|", a.get("technique"))