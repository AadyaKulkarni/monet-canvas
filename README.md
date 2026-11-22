# Monet Canvas

A real-time, in-browser painting tool that turns rough color sketches into Monet-style paintings. The model runs entirely on your device, so there's no server and nothing is uploaded.

**Status:** in development

## How it works

1. Paint rough shapes and colors on the canvas.
2. A small neural network, running in your browser via WebGPU (with a WASM fallback), renders them as an impressionist painting.

## Project structure

- `ml/`: Python code for data collection, training, evaluation, and ONNX export
- `web/`: the website (Vite + TypeScript)
  - `src/engine/`: model loading, inference, and rendering (no UI code)
  - `src/ui/`: canvas, toolbar, and pages

## Tech

PyTorch · ONNX · onnxruntime-web (WebGPU) · TypeScript · Vite

## Roadmap

- [ ] Live site with a drawing canvas
- [ ] Monet dataset from public-domain museum collections
- [ ] Baseline model trained
- [ ] Real-time in-browser inference
- [ ] Evaluation (FID/KID, blind test, latency across devices)
- [ ] Browser extension

## Data

Training images come from public-domain and open-access museum collections. Sources and licenses