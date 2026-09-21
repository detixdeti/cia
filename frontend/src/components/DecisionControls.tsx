// Entscheidung zu einem Vorschlag (F5): annehmen, verwerfen oder zurueckstellen.
//
// Das Werkzeug schlaegt vor, der Mensch entscheidet. Eine Entscheidung aendert
// den Vorschlag des Modells nicht. Eine eigene Ueberarbeitung steht daneben
// (Konzept 4.6). Einen Vorschlag mit Problem kann man verwerfen oder
// zurueckstellen, aber nicht annehmen (Konzept 4.10).

import { useState } from 'react'
import { Check, Clock, X } from 'lucide-react'
import { api, ApiError } from '../api'
import { DECISION } from '../labels'
import type { Decision } from '../types'
import { Badge, ErrorBox } from './ui'

interface Props {
  scenarioId: string
  runId: string
  /** Klasse (Anforderungsrichtung) oder Use Case (Gegenrichtung). */
  subjectId: string
  entryIndex: number
  current: Decision | undefined
  /** Gruende, die eine Annahme verhindern. Leer heisst: annehmbar. */
  blockers: string[]
  /** Nur im Zustand "zur Pruefung bereit" kann entschieden werden. */
  enabled: boolean
  acceptLabel: string
  rejectLabel: string
  onDecided: () => void
}

export function DecisionControls({
  scenarioId,
  runId,
  subjectId,
  entryIndex,
  current,
  blockers,
  enabled,
  acceptLabel,
  rejectLabel,
  onDecided,
}: Props) {
  const [revision, setRevision] = useState('')
  const [busy, setBusy] = useState(false)
  const [problems, setProblems] = useState<string[] | null>(null)

  async function decide(kind: 'accepted' | 'rejected' | 'deferred') {
    setBusy(true)
    setProblems(null)
    try {
      await api.decide(scenarioId, {
        run_id: runId,
        subject_id: subjectId,
        entry_index: entryIndex,
        kind,
        revised_proposal: kind === 'accepted' && revision.trim() !== '' ? revision : undefined,
      })
      setRevision('')
      onDecided()
    } catch (e) {
      setProblems(e instanceof ApiError ? e.problems : [String(e)])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="font-medium text-slate-700">Ihre Entscheidung:</span>
        {current ? <Badge tone="accent">{DECISION[current.kind]}</Badge> : <Badge tone="warn">noch nicht entschieden</Badge>}
      </div>
      {current?.revised_proposal && (
        <div className="mt-2">
          <p className="text-xs text-slate-500">Ihre Überarbeitung (der Vorschlag des Modells bleibt unverändert):</p>
          <div className="text-block mt-1">{current.revised_proposal}</div>
        </div>
      )}

      {enabled ? (
        <>
          {blockers.length > 0 && (
            <p className="mt-2 text-xs text-amber-800">Annehmen ist nicht möglich: {blockers.join('; ')}.</p>
          )}
          <label className="field-label mt-3 text-xs">
            Eigene Überarbeitung des Vorschlags (optional, nur zusammen mit Annehmen)
          </label>
          <textarea className="input" rows={2} value={revision} onChange={(e) => setRevision(e.target.value)} />
          <div className="mt-2 flex flex-wrap gap-2">
            <button className="btn btn-primary btn-sm" disabled={busy || blockers.length > 0} onClick={() => decide('accepted')}>
              <Check className="size-3.5" aria-hidden />
              {acceptLabel}
            </button>
            <button className="btn btn-sm" disabled={busy} onClick={() => decide('rejected')}>
              <X className="size-3.5" aria-hidden />
              {rejectLabel}
            </button>
            <button className="btn btn-quiet btn-sm" disabled={busy} onClick={() => decide('deferred')}>
              <Clock className="size-3.5" aria-hidden />
              Zurückstellen
            </button>
          </div>
          <ErrorBox problems={problems} />
        </>
      ) : (
        <p className="mt-2 text-xs text-slate-500">Entscheiden ist nur im Zustand „zur Prüfung bereit“ möglich.</p>
      )}
    </div>
  )
}
