import type { Renderer } from '../engine/renderer';
import { DrawingCanvas } from './drawing-canvas';

const PALETTE = [
  { name: 'Sky blue', color: '#8fb8de' },
  { name: 'Water', color: '#4f8fa3' },
  { name: 'Lily green', color: '#6a9a5b' },
  { name: 'Deep green', color: '#3d6b45' },
  { name: 'Pink', color: '#e3a0b8' },
  { name: 'Lilac', color: '#a99ad1' },
  { name: 'Yellow', color: '#e8d27a' },
  { name: 'Orange', color: '#e09a5a' },
  { name: 'Eraser (white)', color: '#ffffff' },
];

export async function mountApp(root: HTMLElement, renderer: Renderer): Promise<void> {
  await renderer.init();

  root.innerHTML = `
    <header>
      <h1>Monet Canvas</h1>
      <p class="tag">Paint rough shapes and colors. The right side is a placeholder render for now.</p>
    </header>
    <section class="toolbar">
      <div class="swatches" id="swatches"></div>
      <label class="size">Brush <input id="size" type="range" min="4" max="48" value="16" /></label>
      <button id="undo" type="button">Undo</button>
      <button id="clear" type="button">Clear</button>
    </section>
    <section class="panes">
      <figure><div id="draw-host"></div><figcaption>Your sketch</figcaption></figure>
      <figure><canvas id="out" width="256" height="256"></canvas><figcaption>Rendered (placeholder)</figcaption></figure>
    </section>
  `;

  const drawing = new DrawingCanvas(256);
  root.querySelector<HTMLDivElement>('#draw-host')!.appendChild(drawing.canvas);

  const outCanvas = root.querySelector<HTMLCanvasElement>('#out')!;
  const outCtx = outCanvas.getContext('2d')!;

  // Swatches
  const swatchHost = root.querySelector<HTMLDivElement>('#swatches')!;
  PALETTE.forEach((p, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'swatch' + (i === 1 ? ' active' : '');
    b.style.background = p.color;
    b.title = p.name;
    b.addEventListener('click', () => {
      drawing.color = p.color;
      swatchHost.querySelectorAll('.swatch').forEach((s) => s.classList.remove('active'));
      b.classList.add('active');
    });
    swatchHost.appendChild(b);
  });

  // Controls
  root.querySelector<HTMLInputElement>('#size')!.addEventListener('input', (e) => {
    drawing.size = Number((e.target as HTMLInputElement).value);
  });
  root.querySelector<HTMLButtonElement>('#undo')!.addEventListener('click', () => drawing.undo());
  root.querySelector<HTMLButtonElement>('#clear')!.addEventListener('click', () => drawing.clear());
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') {
      e.preventDefault();
      drawing.undo();
    }
  });

  // Render loop: at most one render per frame, never overlapping.
  let busy = false;
  let dirty = false;
  let queued = false;

  async function refresh(): Promise<void> {
    if (busy) { dirty = true; return; }
    busy = true;
    do {
      dirty = false;
      const out = await renderer.render(drawing.getImageData());
      outCtx.putImageData(out, 0, 0);
    } while (dirty);
    busy = false;
  }

  drawing.onChange = () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; void refresh(); });
  };

  void refresh();
}