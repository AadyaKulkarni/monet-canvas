import requests

URL = "https://api.artic.edu/api/v1/artworks/search"
PARAMS = {"q": "Claude Monet", "fields": "id,title", "limit": 1}

variants = {
    "1. requests default headers": {},
    "2. plain User-Agent": {"User-Agent": "monet-canvas-research/0.1"},
    "3. AIC-User-Agent": {
        "User-Agent": "monet-canvas-research/0.1",
        "AIC-User-Agent": "monet-canvas (YOUR_EMAIL@example.com)",
    },
    "4. browser-like User-Agent": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    },
}

for name, headers in variants.items():
    try:
        r = requests.get(URL, params=PARAMS, headers=headers, timeout=(15, 60))
        print(name, "->", r.status_code, "|", r.text[:120].replace("\n", " "))
    except Exception as e:
        print(name, "-> ERROR", type(e).__name__)