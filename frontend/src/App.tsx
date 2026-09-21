// Einstieg: Kopfzeile mit Ausgangsstand und Modellanbieter, darunter entweder
// die Import-Seite oder der Arbeitsbereich.

import { useState } from 'react'
import { Boxes, ChevronDown, FlaskConical, Moon, Network, Plus, ServerOff, Sun } from 'lucide-react'
import { api } from './api'
import { ImportPage } from './components/ImportPage'
import { ErrorBox, Loading } from './components/ui'
import { Workspace } from './components/Workspace'
import { setTheme, useTheme } from './theme'
import { useLoad } from './useLoad'
import type { Info } from './types'

/** Zeigt dauerhaft, welcher Anbieter antwortet, damit Beispielantworten nicht
 *  mit echten Bewertungen verwechselt werden. */
function ProviderBanner({ info }: { info: Info }) {
  const isPlaceholder = info.provider === 'demo' || info.provider === 'mock'
  return (
    <div
      className={
        isPlaceholder
          ? 'border-b border-amber-200/70 bg-amber-50/80 text-amber-900 backdrop-blur'
          : 'border-b border-slate-200 bg-surface/60 text-slate-600 backdrop-blur'
      }
    >
      <div className="mx-auto flex max-w-[1800px] items-center gap-2 px-5 py-2 text-sm">
        <FlaskConical className="size-4 shrink-0" aria-hidden />
        {info.provider === 'demo' && (
          <span>
            <strong>Demo-Modus.</strong> Die Antworten des Modells sind Beispiele mit „[DEMO]“, keine Bewertung. Nicht
            für Messungen oder die Nutzerstudie verwenden.
          </span>
        )}
        {info.provider === 'mock' && (
          <span>
            <strong>Kein Modell angebunden.</strong> Die Analyse bewertet nichts, alle Methoden und Use Cases bleiben
            offen.
          </span>
        )}
        {!isPlaceholder && <span>Modell: {info.provider}</span>}
      </div>
    </div>
  )
}

/** Wechselt zwischen hellem und dunklem Erscheinungsbild. */
function ThemeToggle() {
  const theme = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <button
      className="btn btn-quiet size-9 !p-0"
      onClick={() => setTheme(next)}
      aria-label={next === 'dark' ? 'Dunkles Erscheinungsbild' : 'Helles Erscheinungsbild'}
      title={next === 'dark' ? 'Dunkel' : 'Hell'}
    >
      {theme === 'dark' ? <Sun className="size-[1.1rem]" aria-hidden /> : <Moon className="size-[1.1rem]" aria-hidden />}
    </button>
  )
}

export default function App() {
  const info = useLoad(() => api.info(), [])
  const baselines = useLoad(() => api.baselines(), [])
  const [chosen, setChosen] = useState<string | null>(null)
  const [importing, setImporting] = useState(false)

  const list = baselines.data ?? []
  // Ohne Wahl gilt der zuletzt importierte Stand.
  const activeId = chosen ?? list[list.length - 1]?.baseline_id ?? null
  const showImport = importing || (baselines.data !== null && list.length === 0)

  return (
    <div className="flex min-h-screen flex-col">
      <header className="glass sticky top-0 z-30 border-x-0 border-t-0">
        <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4 px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-sky-500 text-white shadow-lg shadow-indigo-500/30">
              <Network className="size-5" aria-hidden />
            </div>
            <div>
              <h1 className="text-[0.95rem] leading-tight font-semibold tracking-tight text-slate-900">
                Change Impact Analysis
              </h1>
              <p className="text-xs text-slate-500">Anforderungen und Code im Graphen</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {list.length > 0 && (
              <label className="relative flex items-center" aria-label="Ausgangsstand">
                <Boxes className="pointer-events-none absolute left-3 size-4 text-slate-400" aria-hidden />
                <select
                  value={activeId ?? ''}
                  onChange={(e) => setChosen(e.target.value)}
                  className="input w-auto appearance-none py-1.5 pr-9 pl-9"
                >
                  {list.map((b) => (
                    <option key={b.baseline_id} value={b.baseline_id}>
                      {b.label}
                      {b.has_errors ? ' (mit Fehlern)' : ''}
                    </option>
                  ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-3 size-4 text-slate-400" aria-hidden />
              </label>
            )}
            <ThemeToggle />
            <button className="btn btn-primary" onClick={() => setImporting(true)}>
              <Plus className="size-4" aria-hidden />
              Neuer Ausgangsstand
            </button>
          </div>
        </div>
      </header>

      {info.data && <ProviderBanner info={info.data} />}
      {info.error && (
        <div className="border-b border-red-200 bg-red-50 text-red-800">
          <div className="mx-auto flex max-w-[1800px] items-center gap-2 px-5 py-2 text-sm">
            <ServerOff className="size-4 shrink-0" aria-hidden />
            Das Backend ist nicht erreichbar: {info.error}
          </div>
        </div>
      )}

      <main className="mx-auto w-full max-w-[1800px] flex-1 px-5 py-5">
        {baselines.error && <ErrorBox problems={baselines.error} />}
        {baselines.loading && !baselines.error && <Loading what="Lade Ausgangsstände" />}

        {showImport && (
          <ImportPage
            canCancel={list.length > 0}
            onCancel={() => setImporting(false)}
            onUse={(id) => {
              baselines.reload()
              setChosen(id)
              setImporting(false)
            }}
          />
        )}

        {!showImport && activeId !== null && <Workspace key={activeId} baselineId={activeId} />}
      </main>
    </div>
  )
}
