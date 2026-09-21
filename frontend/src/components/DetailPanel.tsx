// Details zur Auswahl im Graphen (F2): Text eines Use Cases oder Methoden einer
// Klasse, dazu die Verknuepfungen. Die Verknuepfungen kommen aus dem Teilgraphen
// der Auswahl. Es wird nur ein Schritt weit gegangen, nicht ueber gemeinsame
// Klassen hinaus (Konzept 4.3).

import { MousePointerClick } from 'lucide-react'
import { api } from '../api'
import { isUseCaseNode, refOf, signatureText } from '../format'
import { useLoad } from '../useLoad'
import type { Graph } from '../types'
import { Badge, ErrorBox, Loading, Notice, Section } from './ui'

interface Props {
  baselineId: string
  selectedIds: string[]
  /** Der Teilgraph der aktuellen Auswahl, oder ``null`` solange er lädt. */
  subgraph: Graph | null
  onlySubgraph: boolean
  onToggleOnlySubgraph: (value: boolean) => void
}

export function DetailPanel({ baselineId, selectedIds, subgraph, onlySubgraph, onToggleOnlySubgraph }: Props) {
  if (selectedIds.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 px-4 py-10 text-center">
        <div className="grid size-12 place-items-center rounded-full bg-indigo-50 text-indigo-600">
          <MousePointerClick className="size-6" aria-hidden />
        </div>
        <h3 className="font-semibold text-slate-900">Nichts ausgewählt</h3>
        <p className="max-w-xs text-sm text-slate-500">
          Wählen Sie im Graphen einen Use Case oder eine Klasse aus. Sie sehen dann die Verknüpfungen in beide
          Richtungen und die Details.
        </p>
      </div>
    )
  }

  const focus = selectedIds[selectedIds.length - 1]
  const neighbours = subgraph?.nodes.filter((n) => n.selected === false) ?? []

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-slate-600">
          <strong className="text-slate-900">{selectedIds.length}</strong> Knoten ausgewählt
        </p>
        <label className="check">
          <input
            data-testid="only-subgraph"
            type="checkbox"
            checked={onlySubgraph}
            onChange={(e) => onToggleOnlySubgraph(e.target.checked)}
          />
          Nur den Teilgraphen zeigen
        </label>
      </div>

      <Section title="Direkt verknüpft">
        {subgraph === null ? (
          <Loading />
        ) : neighbours.length === 0 ? (
          <Notice tone="warn">
            Keine deklarierte Zuordnung. Das heißt nicht, dass eine Änderung diesen Knoten unberührt lässt.
          </Notice>
        ) : (
          <ul className="flex flex-wrap gap-1.5">
            {neighbours.map((n) => (
              <li key={n.id}>
                <Badge tone="accent">{n.kind === 'class' ? n.ref : n.label}</Badge>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <hr className="my-5 border-slate-200" />
      {isUseCaseNode(focus) ? (
        <UseCaseDetails baselineId={baselineId} id={refOf(focus)} />
      ) : (
        <ClassDetails baselineId={baselineId} id={refOf(focus)} />
      )}
    </div>
  )
}

function UseCaseDetails({ baselineId, id }: { baselineId: string; id: string }) {
  const { data, error, loading } = useLoad(() => api.useCase(baselineId, id), [baselineId, id])
  if (error) return <ErrorBox problems={error} />
  if (loading || data === null) return <Loading />
  return (
    <div>
      <p className="eyebrow">Use Case</p>
      <h3 className="mt-1 flex flex-wrap items-center gap-2 text-base font-semibold text-slate-900">
        {data.id}: {data.title}
        {!data.linked && <Badge tone="warn">nicht zugeordnet</Badge>}
      </h3>
      <div className="text-block mt-3">{data.text || '(kein Text)'}</div>
      {data.source_file && <p className="mt-2 text-xs text-slate-500">Datei: {data.source_file}</p>}
    </div>
  )
}

function ClassDetails({ baselineId, id }: { baselineId: string; id: string }) {
  const { data, error, loading } = useLoad(() => api.classDetail(baselineId, id), [baselineId, id])
  if (error) return <ErrorBox problems={error} />
  if (loading || data === null) return <Loading />
  return (
    <div>
      <p className="eyebrow">Klasse</p>
      <h3 className="mt-1 flex flex-wrap items-center gap-2 text-base font-semibold text-slate-900">
        {data.file_name}
        {!data.linked && <Badge tone="warn">nicht zugeordnet</Badge>}
        {!data.parsed && <Badge tone="error">nicht verarbeitet</Badge>}
      </h3>
      <p className="font-mono text-xs text-slate-500">{data.relative_path}</p>
      {!data.parsed && data.parse_error && <p className="mt-1 text-xs text-red-700">{data.parse_error}</p>}

      <h4 className="mt-4 mb-2 text-sm font-semibold text-slate-700">Methoden ({data.methods.length})</h4>
      {data.methods.length === 0 && <p className="text-sm text-slate-500">Keine Methoden erkannt.</p>}
      <div className="space-y-1.5">
        {data.methods.map((m) => (
          <details key={signatureText(m.ref.signature) + m.ref.source_range.start_byte} className="disclosure">
            <summary>
              <code>{signatureText(m.ref.signature)}</code>
              <span className="ml-2 text-xs font-normal text-slate-400">
                Zeile {m.ref.source_range.start_line}–{m.ref.source_range.end_line}
              </span>
            </summary>
            <pre className="code-block">{m.source}</pre>
          </details>
        ))}
      </div>
    </div>
  )
}
