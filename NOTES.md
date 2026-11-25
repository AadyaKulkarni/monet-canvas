# Notes

## Phase 0 smoke test (tiny 2-layer conv model, 256x256, average of 10 runs)
- webgpu: 30.9 ms
- wasm: 5.4 ms
- Machine: <your laptop and GPU>, Chrome <version>
- Phone result: <what the live site showed on your phone>


## Phase 1: data (done)
- Training data: Kaggle Berkeley Monet dataset, 1,193 JPGs, all 256x256 RGB, no exact duplicates. The Kaggle license is listed as unknown, so the data stays gitignored (ml/data) and is not redistributed.
- Splits (seed 42, by file): train 1073 / val 60 / test 60. File lists are in ml/splits/*.txt.
- Extra clean-license paintings: 33 Monet paintings from the Art Institute of Chicago (ml/data/raw/aic), kept for demo images and a held-out test set. The Met API gave no downloadable Monets.
- Blob function: ml/scripts/blobify.py. random_blobify() draws grid in {20, 24, 32, 40}, 6-12 colors, blur 2.5-4.5, saturation 1.3-1.7.
- Museum APIs: the Met v1 search was retired on 2026-10-01 (use v1.1). The Art Institute API needs an AIC-User-Agent header, read from the AIC_CONTACT environment variable.


## Phase 2: baseline model (done for now)
- Model: ml/scripts/model.py, a small U-Net with 1.78M parameters and a tanh output. It uses only plain convolutions, nearest-neighbor upsampling, batch norm and LeakyReLU so it exports cleanly to ONNX/WebGPU.
- Speed on a GTX 1650 (4 GB): about 12 s/epoch for the L1-only run (batch 16, 0.8 GB), about 78 s/epoch with the GAN losses (batch 8, 1.9 GB).
- L1-only baseline (train.py, 100 epochs): val L1 about 0.146-0.150. Clean but smooth: it tidies the blobs and adds no texture. Use best.pt, not last.pt.
- GAN (train_gan.py: adversarial + VGG perceptual + L1 x50). With an instance-norm discriminator, D won outright (D loss about 0.002, adv 1.0) and the output was grainy. With a spectral-norm discriminator and lr_d 1e-4 (run gan20b, 20 epochs): stable (D about 0.04, adv about 0.9), adds a fine canvas-like texture and some invented detail such as clouds, but no real brushstrokes. Val L1 about 0.152-0.157.
- Decision: ship the 1.78M U-Net with the gan20b weights first, and return to quality later.