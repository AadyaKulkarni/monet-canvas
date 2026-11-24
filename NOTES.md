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