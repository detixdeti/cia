// Meldet dem Backend, was die Oberflaeche angezeigt hat (Konzept 4.13).
//
// Das Protokoll soll erkennen lassen, welche Markierungen, Vergleiche und
// Kontextangaben der Anwender tatsaechlich gesehen hat. Jede Anzeige wird
// pro Seitenaufruf nur einmal gemeldet. Ein Fehler beim Melden stoert die
// Arbeit nicht.

import { api } from './api'
import type { UiEventType } from './types'

const alreadyReported = new Set<string>()

export function reportShown(scenarioId: string, type: UiEventType, subject: string): void {
  const key = `${scenarioId}|${type}|${subject}`
  if (alreadyReported.has(key)) return
  alreadyReported.add(key)
  api.event(scenarioId, type, subject).catch(() => {
    // Nicht kritisch: Die Anzeige selbst funktioniert auch ohne Meldung.
  })
}
