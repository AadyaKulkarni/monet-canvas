export interface Renderer {
  init(): Promise<void>;
  render(src: ImageData): Promise<ImageData>;
}

function clamp(v: number): number {
  return v < 0 ? 0 : v > 255 ? 255 : v;
}

// Stand-in for the real model: box blur + saturation boost.
export class PlaceholderRenderer implements Renderer {
  async init(): Promise<void> {}

  async render(src: ImageData): Promise<ImageData> {
    const { width: w, height: h, data } = src;
    const out = new ImageData(w, h);
    const o = out.data;
    const R = 2;
    const SAT = 1.35;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let r = 0, g = 0, b = 0, n = 0;
        for (let dy = -R; dy <= R; dy++) {
          const yy = y + dy;
          if (yy < 0 || yy >= h) continue;
          for (let dx = -R; dx <= R; dx++) {
            const xx = x + dx;
            if (xx < 0 || xx >= w) continue;
            const i = (yy * w + xx) * 4;
            r += data[i]; g += data[i + 1]; b += data[i + 2];
            n++;
          }
        }
        r /= n; g /= n; b /= n;
        const avg = (r + g + b) / 3;
        const j = (y * w + x) * 4;
        o[j] = clamp(avg + (r - avg) * SAT);
        o[j + 1] = clamp(avg + (g - avg) * SAT);
        o[j + 2] = clamp(avg + (b - avg) * SAT);
        o[j + 3] = 255;
      }
    }
    return out;
  }
}