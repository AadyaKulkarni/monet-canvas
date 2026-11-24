import requests

r = requests.get(
    "https://collectionapi.metmuseum.org/public/collection/v1.1/search",
    params={
        "q": "Claude Monet",
        "artistOrCulture": "true",
        "hasImages": "true",
        "isPublicDomain": "true",
        "offset": 0,
        "limit": 5,
    },
    timeout=30,
)
print("status:", r.status_code)
r.raise_for_status()
data = r.json()
print("total:", data["total"])
print("first ids:", (data["objectIDs"] or [])[:5])