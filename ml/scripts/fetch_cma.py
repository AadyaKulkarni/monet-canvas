import json
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://openaccess-api.clevelandart.org/api/artworks/"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "cma"
TIMEOUT = (15, 60)

session = requests.Session()
session.headers.update({"User-Agent": "monet-canvas-research/0.1"})
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=5, connect=5, read=5, backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504])))


def search_works():
    works = []
    for skip in range(0, 300, 100):
        r = session.get(
            URL,
            params={"q": "monet", "cc0": 1, "has_image": 1, "limit": 100, "skip": skip},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        rows = r.json().get("data") or []
        if not rows:
            break
        works.extend(rows)
    return works


def skip_reason(a):
    creators = " ".join(c.get("description", "") for c in (a.get("creators") or []))
    if "Claude Monet" not in creators:
        return "not by Monet"
    if a.get("share_license_status") != "CC0":
        return "not CC0"
    if not ((a.get("images") or {}).get("web") or {}).get("url"):
        return "no image"
    if a.get("type") != "Painting":
        return "not a painting (" + str(a.get("type")) + ")"
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    works = search_works()
    print("search results:", len(works))

    kept, failed, skipped = [], [], Counter()
    for a in works:
        reason = skip_reason(a)
        if reason:
            skipped[reason] += 1
            if reason != "not by Monet":
                print("skipped:", a["id"], a.get("title"), "|", reason)
            continue

        path = OUT / f"{a['id']}.jpg"
        try:
            if not path.exists():
                resp = session.get(a["images"]["web"]["url"], timeout=(15, 120))
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.save(path, "JPEG", quality=95)
                time.sleep(0.5)
        except (requests.RequestException, OSError, ValueError) as e:
            failed.append(a["id"])
            print("FAILED:", a["id"], type(e).__name__)
            continue

        kept.append({
            "source": "cma",
            "id": a["id"],
            "title": a.get("title"),
            "date": a.get("creation_date"),
            "medium": a.get("technique"),
            "url": a.get("url"),
            "file": path.name,
            "width": img.width if path.exists() else None,
        })
        print("kept:", a["id"], a.get("title"))

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