// Bericht ueber einen Import (Konzept 4.2): Zaehlwerte und Befunde.
// Fehler stehen offen da. Nichts wird uebergangen, und Artefakte ohne
// Zuordnung gelten nicht als unbeeintraechtigt (Konzept 4.1).

import { CircleX, Info, TriangleAlert } from 'lucide-react'
import { IMPORT_COUNT, SEVERITY } from '../labels'
import type { BaselineDetail, Severity } from '../types'
import { Badge, type Tone } from './ui'

const TONE: Record<Severity, Tone> = { error: 'error', warning: 'warn', info: 'muted' }
const ICON = { error: CircleX, warning: TriangleAlert, info: Info }
const ORDER: Severity[] = ['error', 'warning', 'info']

/** Zaehler, bei denen ein Wert ueber null Aufmerksamkeit verdient. */
const NEEDS_ATTENTION = new Set(['unlinked_classes', 'unlinked_use_cases', 'duplicate_link_lines'])

export function ImportReport({ report }: { report: BaselineDetail }) {
  const grouped = ORDER.map((severity) => ({
    severity,
    entries: report.diagnostic_entries.filter((d) => d.severity === severity),
  })).filter((g) => g.entries.length > 0)

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-slate-900">Ausgangsstand „{report.label}“</h3>
        {report.has_errors ? <Badge tone="error">mit Fehlern importiert</Badge> : <Badge tone="accent">importiert</Badge>}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {Object.entries(IMPORT_COUNT).map(([key, label]) => {
          const value = report.counts[key] ?? 0
          const attention = NEEDS_ATTENTION.has(key) && value > 0
          return (
            <div
              key={key}
              className={`rounded-xl border px-3 py-2 ${
                attention ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-slate-50'
              }`}
            >
              <div className="text-xl font-semibold text-slate-900 tabular-nums">{value}</div>
              <div className="text-xs text-slate-500">{label}</div>
            </div>
          )
        })}
      </div>
      <p className="mt-2 text-xs text-slate-500">
        „Ohne Zuordnung“ heißt nicht, dass eine Änderung diese Artefakte unberührt lässt. Es gibt nur keinen
        deklarierten Link.
      </p>

      <div className="mt-5 space-y-4">
        {grouped.length === 0 && <p className="text-sm text-slate-500">Keine Befunde.</p>}
        {grouped.map((group) => {
          const Icon = ICON[group.severity]
          return (
            <div key={group.severity}>
              <h4 className="mb-1.5 flex items-center gap-2 text-sm font-semibold text-slate-700">
                <Badge tone={TONE[group.severity]}>{SEVERITY[group.severity]}</Badge>
                {group.entries.length}
              </h4>
              <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-surface">
                {group.entries.map((d, i) => (
                  <li key={i} className="flex gap-2 px-3 py-2 text-sm text-slate-700">
                    <Icon className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />
                    <span>
                      {d.message}
                      {d.source_file && (
                        <span className="ml-1 font-mono text-xs text-slate-400">
                          [{d.source_file}
                          {d.line_number ? `:${d.line_number}` : ''}]
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </div>
  )
}
