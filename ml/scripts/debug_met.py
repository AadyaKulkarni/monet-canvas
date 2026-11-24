import requests

BASE = "https://collectionapi.metmuseum.org/public/collection"
T = (15, 60)


def obj(oid):
    return requests.get(f"{BASE}/v1/objects/{oid}", timeout=T).json()


# 1) Control: a work that is known to be Open Access (Van Gogh, Wheat Field with Cypresses)
c = obj(436535)
print("control 436535 -> isPublicDomain:", c.get("isPublicDomain"),
      "| image:", "yes" if c.get("primaryImage") else "EMPTY")

# 2) Broader search: "Monet", only public-domain + images, no artistOrCulture filter
r = requests.get(
    f"{BASE}/v1.1/search",
    params={"q": "Monet", "hasImages": "true", "isPublicDomain": "true",
            "offset": 0, "limit": 100},
    timeout=T,
)
d = r.json()
ids = d.get("objectIDs") or []
print("search total:", d.get("total"), "| fetched ids:", len(ids))

pd_monet = []
for oid in ids:
    try:
        o = obj(oid)
    except Exception as e:
        print(oid, "ERROR", type(e).__name__)
        continue
    if "Monet" in o.get("artistDisplayName", "") and o.get("isPublicDomain") and o.get("primaryImage"):
        pd_monet.append((oid, o.get("title"), o.get("classification")))

print("public-domain Monet works with an image:", len(pd_monet))
for row in pd_monet[:15]:
    print("  ", row)