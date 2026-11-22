type Point = { x: number; y: number };

export class DrawingCanvas {
  readonly canvas: HTMLCanvasElement;
  color = '#4f8fa3';
  size = 16;
  onChange: () => void = () => {};

  private ctx: CanvasRenderingContext2D;
  private undoStack: ImageData[] = [];
  private drawing = false;
  private last: Point | null = null;

  constructor(resolution = 256) {
    this.canvas = document.createElement('canvas');
    this.canvas.width = resolution;
    this.canvas.height = resolution;
    this.canvas.className = 'draw-canvas';
    const ctx = this.canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) throw new Error('2D canvas not supported');
    this.ctx = ctx;
    this.fillWhite();

    this.canvas.addEventListener('pointerdown', (e) => this.onDown(e));
    this.canvas.addEventListener('pointermove', (e) => this.onMove(e));
    this.canvas.addEventListener('pointerup', () => this.onUp());
    this.canvas.addEventListener('pointercancel', () => this.onUp());
  }

  getImageData(): ImageData {
    return this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
  }

  undo(): void {
    const prev = this.undoStack.pop();
    if (!prev) return;
    this.ctx.putImageData(prev, 0, 0);
    this.onChange();
  }

  clear(): void {
    this.pushUndo();
    this.fillWhite();
    this.onChange();
  }

  private fillWhite(): void {
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  private pushUndo(): void {
    this.undoStack.push(this.getImageData());
    if (this.undoStack.length > 30) this.undoStack.shift();
  }

  // Convert screen coordinates to canvas pixels (the canvas is scaled by CSS).
  private pos(e: PointerEvent): Point {
    const r = this.canvas.getBoundingClientRect();
    return {
      x: ((e.clientX - r.left) * this.canvas.width) / r.width,
      y: ((e.clientY - r.top) * this.canvas.height) / r.height,
    };
  }

  private onDown(e: PointerEvent): void {
    this.canvas.setPointerCapture(e.pointerId);
    this.pushUndo();
    this.drawing = true;
    const p = this.pos(e);
    this.last = p;
    this.ctx.fillStyle = this.color;
    this.ctx.beginPath();
    this.ctx.arc(p.x, p.y, this.size / 2, 0, Math.PI * 2);
    this.ctx.fill();
    this.onChange();
  }

  private onMove(e: PointerEvent): void {
    if (!this.drawing || !this.last) return;
    const p = this.pos(e);
    this.ctx.strokeStyle = this.color;
    this.ctx.lineWidth = this.size;
    this.ctx.lineCap = 'round';
    this.ctx.lineJoin = 'round';
    this.ctx.beginPath();
    this.ctx.moveTo(this.last.x, this.last.y);
    this.ctx.lineTo(p.x, p.y);
    this.ctx.stroke();
    this.last = p;
    this.onChange();
  }

  private onUp(): void {
    this.drawing = false;
    this.last = null;
    this.onChange();
  }
}