import { defineConfig, defaultClientConditions } from 'vite'

export default defineConfig({
  resolve: {
    conditions: ['onnxruntime-web-use-extern-wasm', ...defaultClientConditions],
  },
  optimizeDeps: { exclude: ['onnxruntime-web'] },
})