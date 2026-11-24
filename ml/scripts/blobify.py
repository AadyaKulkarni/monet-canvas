import random
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ML = Path(__file__).resolve().parents[1]


def blobify(img, grid=32, colors=10, blur=2.0, saturation=1.4):
    """Turn a painting into coarse, flat-ish, saturated color blobs."""
    img = img.convert("RGB")
    small = img.resize((grid, grid), Image.BOX)
    q = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    q = ImageEnhance.Color(q).enhance(saturation)
    big = q.resize(img.size, Image.BICUBIC)
    return big.filter(ImageFilter.GaussianBlur(blur))


def random_blobify(img, rng=random):
    """Randomized settings, used when generating training inputs."""
    return blobify(
        img,
        grid=rng.choice([20, 24, 32, 40]),
        colors=rng.randint(6, 12),
        blur=rng.uniform(2.5, 4.5),
        saturation=rng.uniform(1.3, 1.7),
    )


if __name__ == "__main__":
    lines = (ML / "splits" / "val.txt").read_text().split()
    files = random.Random(1).sample(lines, 8)
    rng = random.Random(7)
    T = 192
    sheet = Image.new("RGB", (8 * T, 4 * T), "white")
    for c, f in enumerate(files):
        im = Image.open(ML / f)
        sheet.paste(im.convert("RGB").resize((T, T)), (c * T, 0))
        for r in range(1, 4):
            sheet.paste(random_blobify(im, rng).resize((T, T)), (c * T, r * T))
    out = ML / "data" / "blob_preview2.jpg"
    sheet.save(out, quality=90)
    print("saved:", out)
    print("rows: original, then 3 random blobify draws")