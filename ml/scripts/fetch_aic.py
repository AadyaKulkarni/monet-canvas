import os
import json
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SEARCH_URL = "https://api.artic.edu/api/v1/artworks/search"
IIIF = "https://www.artic.edu/iiif/2/{}/full/843,/0/default.jpg"
FIELDS = ("id,title,artist_title,date_display,medium_display,"
          "classification_title,is_public_domain,image_id")
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "aic"
TIMEOUT = (15, 60)
NOT_PAINTING = ("print", "drawing", "sketch", "photograph", "book", "sculpture")

session = requests.Session()
session.headers.update({
    "User-Agent": "monet-canvas-research/0.1",
    "AIC-User-Agent": "monet-canvas (" + os.environ["AIC_CONTACT"] + ")",
})
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, connect=5, read=5, backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504])))


def search_works():
    works = []
    for page in range(1, 6):
        r = session.get(
            SEARCH_URL,
            params={
                "q": "Claude Monet",
                "query[term][is_public_domain]": "true",
                "fields": FIELDS,
                "limit": 100,
                "page": page,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json().get("data") or []
        if not rows:
            break
        works.extend(rows)
    return works


def skip_reason(o):
    if "Monet" not in (o.get("artist_title") or ""):
        return "not by Monet"
    if not o.get("is_public_domain"):
        return "not public domain"
    if not o.get("image_id"):
        return "no image"
    cls = (o.get("classification_title") or "").lower()
    medium = (o.get("medium_display") or "").lower()
    title = (o.get("title") or "").lower()
    if title.startswith("caricature"):
        return "caricature"
    if "paper" in medium and "oil" not in medium:
        return "on paper, not oil"
    if "painting" not in cls and "oil" not in medium:
        return "not a painting (" + cls + ")"
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    works = search_works()
    print("search results:", len(works))

    kept, failed, skipped = [], [], Counter()
    for o in works:
        reason = skip_reason(o)
        if reason:
            skipped[reason] += 1
            if reason != "not by Monet":
                print("skipped:", o["id"], o.get("title"), "|", reason)
            continue

        path = OUT / f"{o['id']}.jpg"
        try:
            if not path.exists():
                resp = session.get(IIIF.format(o["image_id"]), timeout=(15, 120))
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.save(path, "JPEG", quality=95)
                time.sleep(1.0)
        except (requests.RequestException, OSError, ValueError) as e:
            failed.append(o["id"])
            print("FAILED:", o["id"], type(e).__name__)
            continue

        kept.append({
            "source": "aic",
            "id": o["id"],
            "title": o.get("title"),
            "date": o.get("date_display"),
            "medium": o.get("medium_display"),
            "url": f"https://www.artic.edu/artworks/{o['id']}",
            "file": path.name,
        })
        print("kept:", o["id"], o.get("title"))

    with open(OUT / "metadata.jsonl", "w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("---")
    print("kept:", len(kept), "of", len(works))
    print("skipped:", dict(skipped))
    print("failed:", failed)
    print("saved to:", OUT)


if __name__ == "__main__":
    main()