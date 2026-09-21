// Kleiner Hilfs-Hook: laedt Daten und liefert Ergebnis, Fehler und Ladezustand.
//
//   const { data, error, loading, reload } = useLoad(() => api.graph(id), [id])
//
// Aendert sich einer der Werte in `deps`, wird neu geladen. `reload()` laedt mit
// denselben Werten erneut, ohne dass die alten Daten kurz verschwinden.

import { useEffect, useState } from 'react'

interface Result<T> {
  key: string
  data: T | null
  error: string | null
}

export function useLoad<T>(loader: () => Promise<T>, deps: (string | number | null)[]) {
  const key = JSON.stringify(deps)
  const [result, setResult] = useState<Result<T> | null>(null)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    loader()
      .then((data) => {
        if (!cancelled) setResult({ key, data, error: null })
      })
      .catch((error: unknown) => {
        const message = error instanceof Error ? error.message : String(error)
        if (!cancelled) setResult({ key, data: null, error: message })
      })
    return () => {
      cancelled = true
    }
    // `loader` ist absichtlich nicht in der Liste: Massgeblich sind `deps`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, version])

  // Ein Ergebnis zaehlt nur, wenn es zu den aktuellen `deps` gehoert.
  const current = result !== null && result.key === key ? result : null
  return {
    data: current?.data ?? null,
    error: current?.error ?? null,
    loading: current === null,
    reload: () => setVersion((v) => v + 1),
  }
}
