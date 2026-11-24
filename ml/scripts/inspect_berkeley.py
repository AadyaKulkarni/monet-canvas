import hashlib
import random
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "berkeley"
OUT = Path(__file__).resolve().parents[1] / "data" / "contact_sheet.jpg"

files = sorted(ROOT.rglob("*.jpg"))
print("files:", len(files))

sizes, modes, seen, dupes = Counter(), Counter(), {}, []
for f in files:
    with Image.open(f) as im:
        sizes[im.size] += 1
        modes[im.mode] += 1
    h = hashlib.md5(f.read_bytes()).hexdigest()
    if h in seen:
        dupes.append((f.name, seen[h]))
    else:
        seen[h] = f.name

print("sizes:", dict(sizes))
print("modes:", dict(modes))
print("exact duplicate files:", len(dupes))

# contact sheet: 48 random images, 8 columns x 6 rows
random.seed(0)
sample = random.sample(files, 48)
T = 192
sheet = Image.new("RGB", (8 * T, 6 * T), "white")
for i, f in enumerate(sample):
    with Image.open(f) as im:
        sheet.paste(im.convert("RGB").resize((T, T)), ((i % 8) * T, (i // 8) * T))
sheet.save(OUT, quality=90)
print("contact sheet saved to:", OUT)