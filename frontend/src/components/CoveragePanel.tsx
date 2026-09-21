// Abdeckungsanzeige und Abschluss eines Szenarios (Konzept 4.8 und 4.12).
//
// Die Zahlen zeigen, wie weit ein Lauf gekommen ist. Sie sind kein
// Qualitaetsnachweis. Die vier Zustaende bleiben getrennt und keiner ist eine
// Entwarnung: nicht zugeordnet, nicht verarbeitet, nicht beurteilbar und "im
// betrachteten Kontext kein Bedarf erkennbar".

import { useState } from 'react'
import { Lock } from 'lucide-react'
import { api, ApiError } from '../api'
import { formatTime } from '../format'
import { COUNT, OPEN_KIND } from '../labels'
import { useLoad } from '../useLoad'
import type { OpenItem, Scenario } from '../types'
import { Badge, ErrorBox, Loading, Notice, Section } from './ui'

interface Props {
  scenario: Scenario
  /** Aendert sich nach jeder Entscheidung oder Analyse und loest ein Neuladen aus. */
  version: number
  onClosed: () => void
}

function groupByKind(items: OpenItem[]): [string, OpenItem[]][] {
  const groups = new Map<string, OpenItem[]>()
  for (const item of items) groups.set(item.kind, [...(groups.get(item.kind) ?? []), item])
  return Array.from(groups.entries())
}

export function CoveragePanel({ scenario, version, onClosed }: Props) {
  const { data, error } = useLoad(() => api.coverage(scenario.scenario_id), [scenario.scenario_id, version])
  const [acknowledged, setAcknowledged] = useState(false)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [problems, setProblems] = useState<string[] | null>(null)

  if (error) return <p className="text-sm text-slate-500">Noch keine Abdeckung: {error}</p>
  if (data === null) return <Loading />

  const { coverage, closure } = data
  const openItems = closure ? closure.open_items : coverage.open_items

  async function close() {
    setBusy(true)
    setProblems(null)
    try {
      await api.close(scenario.scenario_id, {
        acknowledge_open_items: acknowledged,
        note: note.trim() || null,
      })
      onClosed()
    } catch (e) {
      setProblems(e instanceof ApiError ? e.problems : [String(e)])
    } finally {
      setBusy(false)
    }
  }

  return (
    <Section title="Abdeckung und offene Fälle">
      <p className="mb-2 text-xs text-slate-500">
        Diese Zahlen zeigen den Ablauf, nicht die Qualität. Keine davon ist eine Entwarnung.
      </p>
      <dl className="divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 bg-surface text-sm">
        {Object.entries(coverage.counts).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between gap-3 px-3 py-1.5">
            <dt className="text-slate-600">{COUNT[key] ?? key}</dt>
            <dd className="font-semibold text-slate-900 tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>

      <h4 className="mt-5 mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800">
        {closure ? 'Beim Abschluss offen' : 'Offene Fälle'}
        <Badge tone={openItems.length > 0 ? 'warn' : 'neutral'}>{openItems.length}</Badge>
      </h4>
      {openItems.length === 0 && <p className="text-sm text-slate-500">Keine offenen Fälle.</p>}
      <div className="space-y-1.5">
        {groupByKind(openItems).map(([kind, items]) => (
          <details key={kind} open={items.length <= 4} className="disclosure">
            <summary>
              {OPEN_KIND[kind] ?? kind} <span className="font-normal text-slate-500">({items.length})</span>
            </summary>
            <ul className="space-y-1 text-sm">
              {items.map((item, i) => (
                <li key={i}>
                  <code className="font-semibold text-slate-800">{item.ref}</code>{' '}
                  {item.detail && <span className="text-slate-500">– {item.detail}</span>}
                </li>
              ))}
            </ul>
          </details>
        ))}
      </div>

      {closure && (
        <Notice tone="info" className="mt-4">
          <p className="flex items-center gap-1.5 font-semibold">
            <Lock className="size-3.5" aria-hidden />
            Abgeschlossen am {formatTime(closure.closed_at)}
          </p>
          <p className="mt-1">
            {closure.open_items_acknowledged
              ? 'Die offenen Fälle wurden ausdrücklich zur Kenntnis genommen.'
              : 'Es waren keine Fälle offen.'}
          </p>
          {closure.note && <p className="mt-1">Begründung: {closure.note}</p>}
        </Notice>
      )}

      {!closure && scenario.state === 'ready_for_review' && (
        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/60 p-4">
          <h4 className="text-sm font-semibold text-slate-900">Szenario abschließen</h4>
          {openItems.length > 0 && (
            <>
              <label className="check mt-3">
                <input
                  data-testid="ack-open"
                  type="checkbox"
                  checked={acknowledged}
                  onChange={(e) => setAcknowledged(e.target.checked)}
                />
                Ich habe die offenen Fälle zur Kenntnis genommen.
              </label>
              <label className="field-label mt-3">Begründung für den Abschluss trotz offener Fälle</label>
              <textarea
                data-testid="close-note"
                className="input"
                rows={3}
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </>
          )}
          <ErrorBox problems={problems} />
          <button
            className="btn btn-primary mt-3"
            disabled={busy || (openItems.length > 0 && (!acknowledged || note.trim() === ''))}
            onClick={close}
          >
            Abschließen
          </button>
        </div>
      )}
    </Section>
  )
}
