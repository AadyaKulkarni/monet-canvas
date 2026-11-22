import './style.css'
import { PlaceholderRenderer } from './engine/renderer'
import { mountApp } from './ui/app'
import { runSmokeTest } from './engine/smoke-test'

const root = document.querySelector<HTMLDivElement>('#app')!
mountApp(root, new PlaceholderRenderer()).catch(console.error)

const status = document.createElement('pre')
status.id = 'runtime-status'
status.textContent = 'Runtime check: running…'
document.body.appendChild(status)

runSmokeTest()
  .then((results) => {
    status.textContent =
      'Runtime check (tiny model, 256×256, average of 10 runs):\n' +
      results
        .map((r) => (r.ok ? `  ${r.backend}: ${r.ms.toFixed(1)} ms` : `  ${r.backend}: FAILED - ${r.error}`))
        .join('\n')
  })
  .catch((e) => {
    status.textContent = 'Runtime check failed: ' + e
  })