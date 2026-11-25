import random
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision.transforms.functional import to_tensor
from torchvision.utils import save_image

from blobify import random_blobify

ML = Path(__file__).resolve().parents[1]


class BlobMonet(Dataset):
    """Returns (blob, painting) tensors in [-1, 1], shape 3x256x256."""

    def __init__(self, split="train"):
        text = (ML / "splits" / f"{split}.txt").read_text(encoding="utf-8")
        self.files = [line for line in text.splitlines() if line.strip()]
        self.train = split == "train"

    def __len__(self):
        return len(self.files)

    def __getitem__(self, i):
        img = Image.open(ML / self.files[i]).convert("RGB")
        if self.train:
            rng = random  # fresh randomness every time
            if rng.random() < 0.5:
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        else:
            rng = random.Random(1000 + i)  # same blob for the same image, every run
        blob = random_blobify(img, rng)
        return to_tensor(blob) * 2 - 1, to_tensor(img) * 2 - 1


if __name__ == "__main__":
    import time

    ds = BlobMonet("train")
    print("train images:", len(ds), "| val:", len(BlobMonet("val")), "| test:", len(BlobMonet("test")))
    dl = DataLoader(ds, batch_size=8, shuffle=True, num_workers=0)
    t = time.time()
    blob, target = next(iter(dl))
    print("batch time: %.2fs" % (time.time() - t))
    print("blob:", tuple(blob.shape), "| target:", tuple(target.shape))
    print("value range: %.2f to %.2f" % (blob.min(), blob.max()))
    out = ML / "data" / "batch_check.jpg"
    save_image(torch.cat([blob, target]) * 0.5 + 0.5, out, nrow=8)
    print("saved:", out)