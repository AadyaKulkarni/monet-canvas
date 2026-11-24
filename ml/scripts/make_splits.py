import random
from pathlib import Path

ML = Path(__file__).resolve().parents[1]
ROOT = ML / "data" / "raw" / "berkeley"
OUT = ML / "splits"
OUT.mkdir(exist_ok=True)

files = sorted(p.relative_to(ML).as_posix() for p in ROOT.rglob("*.jpg"))
random.Random(42).shuffle(files)

n_val = n_test = 60
splits = {
    "test": files[:n_test],
    "val": files[n_test:n_test + n_val],
    "train": files[n_test + n_val:],
}

for name, items in splits.items():
    (OUT / f"{name}.txt").write_text("\n".join(items) + "\n", encoding="utf-8")
    print(name, len(items))

print("total:", len(files))
print("saved to:", OUT)