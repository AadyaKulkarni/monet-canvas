import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import VGG16_Weights, vgg16
from torchvision.utils import save_image

from dataset import BlobMonet
from model import UNet

ML = Path(__file__).resolve().parents[1]


class PatchD(nn.Module):
    """Judges 30x30 patches of (blob, image) pairs as real or fake.

    Spectral norm limits how sharply the discriminator can separate real
    from fake, which stops it from winning outright against a small generator.
    """

    def __init__(self):
        super().__init__()

        def c(cin, cout, stride):
            return [
                nn.utils.spectral_norm(nn.Conv2d(cin, cout, 4, stride, 1)),
                nn.LeakyReLU(0.2, inplace=True),
            ]

        self.net = nn.Sequential(
            *c(6, 64, 2), *c(64, 128, 2), *c(128, 256, 2), *c(256, 256, 1),
            nn.utils.spectral_norm(nn.Conv2d(256, 1, 4, 1, 1)),
        )

    def forward(self, blob, img):
        return self.net(torch.cat([blob, img], 1))


class Perceptual(nn.Module):
    """L1 distance between frozen VGG16 features at three depths."""

    def __init__(self):
        super().__init__()
        self.f = vgg16(weights=VGG16_Weights.IMAGENET1K_V1).features[:16].eval()
        for p in self.f.parameters():
            p.requires_grad = False
        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def prep(self, x):
        return (x * 0.5 + 0.5 - self.mean) / self.std

    def forward(self, fake, real):
        keep = (3, 8, 15)  # relu1_2, relu2_2, relu3_3
        with torch.no_grad():
            r, feats = self.prep(real), []
            for i, layer in enumerate(self.f):
                r = layer(r)
                if i in keep:
                    feats.append(r)
        x, loss, k = self.prep(fake), 0.0, 0
        for i, layer in enumerate(self.f):
            x = layer(x)
            if i in keep:
                loss = loss + (x - feats[k]).abs().mean()
                k += 1
        return loss


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="gan")
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--bs", type=int, default=8)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--lr_d", type=float, default=1e-4)
    p.add_argument("--adv", type=float, default=1.0)
    p.add_argument("--l1", type=float, default=50.0)
    p.add_argument("--perc", type=float, default=1.0)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--sample_every", type=int, default=5)
    a = p.parse_args()

    dev = "cuda"
    run = ML / "runs" / a.name
    (run / "samples").mkdir(parents=True, exist_ok=True)

    dl = DataLoader(BlobMonet("train"), batch_size=a.bs, shuffle=True,
                    num_workers=a.workers, persistent_workers=a.workers > 0)
    val_dl = DataLoader(BlobMonet("val"), batch_size=10, num_workers=0)
    probe_ds = BlobMonet("val")
    px, py = next(iter(DataLoader(probe_ds, batch_size=8)))
    px, py = px.to(dev), py.to(dev)

    G, D, P = UNet().to(dev), PatchD().to(dev), Perceptual().to(dev)
    oG = torch.optim.Adam(G.parameters(), a.lr, betas=(0.5, 0.999))
    oD = torch.optim.Adam(D.parameters(), a.lr_d, betas=(0.5, 0.999))

    for ep in range(1, a.epochs + 1):
        G.train()
        D.train()
        t0, n = time.time(), 0
        s = dict(D=0.0, adv=0.0, l1=0.0, perc=0.0)
        for x, y in dl:
            x, y = x.to(dev), y.to(dev)
            fake = G(x)

            d_real, d_fake = D(x, y), D(x, fake.detach())
            lossD = 0.5 * (((d_real - 1) ** 2).mean() + (d_fake ** 2).mean())
            oD.zero_grad()
            lossD.backward()
            oD.step()

            adv = ((D(x, fake) - 1) ** 2).mean()
            l1 = (fake - y).abs().mean()
            perc = P(fake, y)
            lossG = a.adv * adv + a.l1 * l1 + a.perc * perc
            oG.zero_grad()
            lossG.backward()
            oG.step()

            n += len(x)
            for k, v in (("D", lossD), ("adv", adv), ("l1", l1), ("perc", perc)):
                s[k] += v.item() * len(x)

        G.eval()
        with torch.no_grad():
            vl = sum((G(x.to(dev)) - y.to(dev)).abs().mean().item() * len(x) for x, y in val_dl) / 60
            out = G(px)
        print("epoch %d | D %.3f | adv %.3f | l1 %.4f | perc %.3f | val L1 %.4f | %.0fs | peak mem %.0f MB"
              % (ep, s["D"] / n, s["adv"] / n, s["l1"] / n, s["perc"] / n, vl,
                 time.time() - t0, torch.cuda.max_memory_allocated() / 2**20), flush=True)
        if ep == 1 or ep % a.sample_every == 0 or ep == a.epochs:
            grid = torch.cat([px, out, py]) * 0.5 + 0.5
            save_image(grid.clamp(0, 1), run / "samples" / f"ep{ep:03d}.jpg", nrow=8)
        torch.save(G.state_dict(), run / "last.pt")
        if ep % 10 == 0:
            torch.save(G.state_dict(), run / f"G_ep{ep:03d}.pt")

    print("done. outputs in", run)


if __name__ == "__main__":
    main()