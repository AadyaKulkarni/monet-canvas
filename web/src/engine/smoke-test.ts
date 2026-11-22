import * as ort from 'onnxruntime-web/webgpu';

export type BenchResult = {
  backend: string;
  ms: number;
  ok: boolean;
  error?: string;
};

async function hasWebGPU(): Promise<boolean> {
  try {
    const gpu = (navigator as any).gpu;
    if (!gpu) return false;
    return (await gpu.requestAdapter()) !== null;
  } catch {
    return false;
  }
}

function configureRuntime(): void {
  const v = ort.env.versions.web;
  if (!v) throw new Error('Could not read onnxruntime-web version');
  // Smoke test only: load the .wasm runtime from a CDN, pinned to the installed
  // version, so we don't ship a very large file with the site yet.
  ort.env.wasm.wasmPaths = `https://cdn.jsdelivr.net/npm/onnxruntime-web@${v}/dist/`;
  // Multi-threaded WASM needs cross-origin isolation headers. We'll add those later.
  ort.env.wasm.numThreads = 1;
}

async function bench(provider: 'webgpu' | 'wasm', runs = 10): Promise<BenchResult> {
  try {
    const session = await ort.InferenceSession.create('/tiny.onnx', {
      executionProviders: [provider],
    });
    const data = new Float32Array(1 * 3 * 256 * 256).fill(0.5);
    const input = new ort.Tensor('float32', data, [1, 3, 256, 256]);

    await session.run({ x: input }); // warm-up: first run includes shader compile / setup
    const t0 = performance.now();
    for (let i = 0; i < runs; i++) await session.run({ x: input });
    return { backend: provider, ms: (performance.now() - t0) / runs, ok: true };
  } catch (e) {
    return { backend: provider, ms: 0, ok: false, error: String(e) };
  }
}

export async function runSmokeTest(): Promise<BenchResult[]> {
  configureRuntime();
  const results: BenchResult[] = [];
  if (await hasWebGPU()) results.push(await bench('webgpu'));
  results.push(await bench('wasm'));
  return results;
}