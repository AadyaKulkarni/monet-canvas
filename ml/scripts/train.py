import argparse
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset
from torchvision.utils import save_image

from dataset import BlobMonet
from model import UNet

ML = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="baseline")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--bs", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--overfit", type=int, default=0, help="train on only N images")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--log_every", type=int, default=1)
    p.add_argument("--sample_every", type=int, default=5)
    a = p.parse_args()

    dev = "cuda"
    run = ML / "runs" / a.name
    (run / "samples").mkdir(parents=True, exist_ok=True)

    train = BlobMonet("train")
    if a.overfit:
        train = Subset(train, range(a.overfit))
    dl = DataLoader(train, batch_size=a.bs, shuffle=True, num_workers=a.workers,
                    persistent_workers=a.workers > 0)
    val_dl = DataLoader(BlobMonet("val"), batch_size=20, num_workers=0)

    # fixed probe batch (deterministic blobs) so sample grids are comparable across epochs
    probe_ds = BlobMonet("train" if a.overfit else "val")
    probe_ds.train = False
    px, py = next(iter(DataLoader(probe_ds, batch_size=8)))
    px, py = px.to(dev), py.to(dev)

    net = UNet().to(dev)
    opt = torch.optim.Adam(net.parameters(), a.lr, betas=(0.5, 0.999))
    best = float("inf")

    for ep in range(1, a.epochs + 1):
        net.train()
        t0 = time.time()
        tot, n = 0.0, 0
        for x, y in dl:
            x, y = x.to(dev), y.to(dev)
            loss = (net(x) - y).abs().mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            tot += loss.item() * len(x)
            n += len(x)

        net.eval()
        with torch.no_grad():
            vtot, vn = 0.0, 0
            for x, y in val_dl:
                x, y = x.to(dev), y.to(dev)
                vtot += (net(x) - y).abs().mean().item() * len(x)
                vn += len(x)
            val_l1 = vtot / vn
            out = net(px)

        if ep == 1 or ep % a.log_every == 0:
            print("epoch %d | train L1 %.4f | val L1 %.4f | %.1fs"
                  % (ep, tot / n, val_l1, time.time() - t0), flush=True)
        if ep == 1 or ep % a.sample_every == 0 or ep == a.epochs:
            grid = torch.cat([px, out, py]) * 0.5 + 0.5  # rows: blob, output, target
            save_image(grid.clamp(0, 1), run / "samples" / f"ep{ep:03d}.jpg", nrow=8)
        torch.save(net.state_dict(), run / "last.pt")
        if val_l1 < best:
            best = val_l1
            torch.save(net.state_dict(), run / "best.pt")

    print("done. best val L1: %.4f | outputs in %s" % (best, run))


if __name__ == "__main__":
    main()