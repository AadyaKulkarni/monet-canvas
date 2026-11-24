import json
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects/{}"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "met"
MAX_SIDE = 2048
TIMEOUT = (15, 60)  # (connect, read) seconds

session = requests.Session()
session.headers.update({"User-Agent": "monet-canvas-research/0.1"})
retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retry))


def search_ids():
    ids, offset, limit = [], 0, 100
    while True:
        r = session.get(
            SEARCH_URL,
            params={
                "q": "Claude Monet",
                "artistOrCulture": "true",
                "hasImages": "true",
                "isPublicDomain": "true",
                "offset": offset,
                "limit": limit,
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        page = data.get("objectIDs") or []
        ids.extend(page)
        offset += limit
        if not page or len(ids) >= data["total"]:
            return ids


def skip_reason(o):
    if "Claude Monet" not in o.get("artistDisplayName", ""):
        return "not by Claude Monet"
    if not o.get("isPublicDomain"):
        return "not public domain"
    if not o.get("primaryImage"):
        return "no image"
    cls = o.get("classification", "").lower()
    medium = o.get("medium", "").lower()
    if "painting" not in cls and "oil" not in medium:
        return "not a painting"
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = search_ids()
    print("candidates:", len(ids))

    kept, failed, skipped = [], [], Counter()
    for oid in ids:
        try:
            o = session.get(OBJECT_URL.format(oid), timeout=TIMEOUT).json()
            time.sleep(0.2)
            reason = skip_reason(o)
            if reason:
                skipped[reason] += 1
                print("skipped:", oid, reason)
                continue

            path = OUT / f"{oid}.jpg"
            if not path.exists():
                resp = session.get(o["primaryImage"], timeout=(15, 120))
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img.thumbnail((MAX_SIDE, MAX_SIDE))
                img.save(path, "JPEG", quality=95)
                time.sleep(0.2)
        except (requests.RequestException, OSError, ValueError) as e:
            failed.append(oid)
            print("FAILED:", oid, type(e).__name__)
            continue

        kept.append(
            {
                "source": "met",
                "id": oid,
                "title": o.get("title"),
                "date": o.get("objectDate"),
                "medium": o.get("medium"),
                "url": o.get("objectURL"),
                "file": path.name,
            }
        )
        print("kept:", oid, o.get("title"))

    with open(OUT / "metadata.jsonl", "w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("---")
    print("kept:", len(kept), "of", len(ids))
    print("skipped:", dict(skipped))
    print("failed:", failed)
    print("saved to:", OUT)


if __name__ == "__main__":
    main()