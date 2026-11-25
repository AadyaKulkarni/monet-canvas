import torch
import torch.nn as nn


def down(cin, cout):
    return nn.Sequential(
        nn.Conv2d(cin, cout, 3, stride=2, padding=1, bias=False),
        nn.BatchNorm2d(cout),
        nn.LeakyReLU(0.2, inplace=True),
    )


def block(cin, cout):
    return nn.Sequential(
        nn.Conv2d(cin, cout, 3, padding=1, bias=False),
        nn.BatchNorm2d(cout),
        nn.LeakyReLU(0.2, inplace=True),
    )


class UNet(nn.Module):
    """Blob image (3x256x256, range -1..1) -> painting (same shape)."""

    def __init__(self):
        super().__init__()
        self.e1 = down(3, 32)      # 128
        self.e2 = down(32, 64)     # 64
        self.e3 = down(64, 128)    # 32
        self.e4 = down(128, 256)   # 16
        self.e5 = down(256, 256)   # 8
        self.up = nn.Upsample(scale_factor=2, mode="nearest")
        self.d4 = block(256 + 256, 128)  # 16
        self.d3 = block(128 + 128, 64)   # 32
        self.d2 = block(64 + 64, 32)     # 64
        self.d1 = block(32 + 32, 32)     # 128
        self.f1 = block(32 + 3, 16)      # 256, sees the input blob again
        self.f2 = nn.Conv2d(16, 3, 3, padding=1)

    def forward(self, x):
        e1 = self.e1(x)
        e2 = self.e2(e1)
        e3 = self.e3(e2)
        e4 = self.e4(e3)
        e5 = self.e5(e4)
        d4 = self.d4(torch.cat([self.up(e5), e4], 1))
        d3 = self.d3(torch.cat([self.up(d4), e3], 1))
        d2 = self.d2(torch.cat([self.up(d3), e2], 1))
        d1 = self.d1(torch.cat([self.up(d2), e1], 1))
        f = self.f1(torch.cat([self.up(d1), x], 1))
        return torch.tanh(self.f2(f))


if __name__ == "__main__":
    import time

    net = UNet().cuda()
    n = sum(p.numel() for p in net.parameters())
    print("params: %.2fM" % (n / 1e6))
    opt = torch.optim.Adam(net.parameters(), 2e-4)
    for bs in (8, 16):
        x = torch.randn(bs, 3, 256, 256, device="cuda").clamp(-1, 1)
        torch.cuda.reset_peak_memory_stats()
        for i in range(13):
            if i == 3:
                torch.cuda.synchronize()
                t = time.time()
            loss = (net(x) - x).abs().mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        torch.cuda.synchronize()
        dt = (time.time() - t) / 10
        mem = torch.cuda.max_memory_allocated() / 2**20
        print("batch %d: %.3f s/iter | peak GPU memory %.0f MB | out %s range %.2f..%.2f"
              % (bs, dt, mem, tuple(net(x).shape), net(x).min(), net(x).max()))