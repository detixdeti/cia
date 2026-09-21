// Hell oder dunkel. Die Wahl steht als Klasse "dark" am <html>-Element und wird im
// Browser gemerkt. Ohne Wahl folgt die Oberflaeche dem System.

import { useSyncExternalStore } from 'react'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'theme'
const CHANGE_EVENT = 'themechange'

export function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

function apply(theme: Theme): void {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  window.dispatchEvent(new Event(CHANGE_EVENT))
}

/** Beim Start aufrufen, bevor etwas gezeichnet wird. */
export function initTheme(): void {
  const saved = localStorage.getItem(STORAGE_KEY)
  const dark = saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  document.documentElement.classList.toggle('dark', dark)
}

export function setTheme(theme: Theme): void {
  localStorage.setItem(STORAGE_KEY, theme)
  apply(theme)
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange)
  return () => window.removeEventListener(CHANGE_EVENT, onChange)
}

/** Das aktuelle Thema. Die Komponente zeichnet sich bei einem Wechsel neu. */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, currentTheme)
}
