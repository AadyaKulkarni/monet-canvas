import './style.css'
import { PlaceholderRenderer } from './engine/renderer'
import { mountApp } from './ui/app'

const root = document.querySelector<HTMLDivElement>('#app')!
mountApp(root, new PlaceholderRenderer()).catch(console.error)