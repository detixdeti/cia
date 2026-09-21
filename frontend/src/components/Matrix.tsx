// Matrixansicht: dieselbe Relation T wie im Graphen, als Tabelle.
//
// Zeilen sind Use Cases, Spalten Klassen, ein Punkt steht fuer einen
// deklarierten Trace-Link (Konzept 4.3). Die Matrix hat keine Kreuzungen und
// bleibt auch bei vielen Artefakten lesbar. Sie teilt Auswahl, Markierungen und
// Teilgraph-Filter mit dem Graphen.
//
// Regeln aus Konzept 4.8 und 4.12:
// - Jeder Zustand steht auch als Text im Kopf einer Zeile oder Spalte.
// - Eine leere Zeile oder Spalte heisst "nicht zugeordnet", nicht "unberuehrt".
// - Die Summen zeigen nur den Knotengrad. Eine Bewertung folgt daraus nicht.

import { useMemo, useState } from 'react'
import { nodeStates, orderColumns, type Highlight } from '../graphLayout'
import type { Graph, GraphNode } from '../types'

interface Props {
  graph: Graph
  selectedIds: string[]
  highlights: Record<string, Highlight>
  /** Nur diese Knoten zeigen. ``null`` zeigt alle. */
  visibleIds: Set<string> | null
  onSelectionChange: (ids: string[]) => void
}

/** Der Titel eines Use Cases ohne die vorangestellte Kennung. */
function titleOf(node: GraphNode): string {
  return node.label.startsWith(`${node.ref}:`) ? node.label.slice(node.ref.length + 1).trim() : node.label
}

/** Farbe eines Kopfes: Auswahl vor Szenario vor Nachbarschaft. */
function headerTone(selected: boolean, highlight: Highlight | undefined, hovered: boolean): string {
  if (selected) return 'bg-indigo-100 text-indigo-900'
  if (highlight === 'changed') return 'bg-rose-50 text-rose-900'
  if (highlight === 'candidate') return 'bg-amber-50 text-amber-900'
  if (highlight === 'neighbor') return 'bg-indigo-50 text-indigo-800'
  if (hovered) return 'bg-slate-100 text-slate-900'
  return 'bg-surface text-slate-700'
}

/** Randmarkierung am Kopf, damit der Szenariozustand auch ohne Text auffaellt. */
function headerEdge(highlight: Highlight | undefined): string {
  if (highlight === 'changed') return 'border-rose-500'
  if (highlight === 'candidate') return 'border-amber-500'
  if (highlight === 'neighbor') return 'border-indigo-400'
  return 'border-transparent'
}

export function Matrix({ graph, selectedIds, highlights, visibleIds, onSelectionChange }: Props) {
  const [hover, setHover] = useState<{ row: string | null; col: string | null }>({ row: null, col: null })

  const { useCases, classes } = useMemo(() => {
    const ordered = orderColumns(graph)
    const shown = (n: GraphNode) => visibleIds === null || visibleIds.has(n.id)
    return { useCases: ordered.useCases.filter(shown), classes: ordered.classes.filter(shown) }
  }, [graph, visibleIds])

  const links = useMemo(() => new Set(graph.edges.map((e) => `${e.source}|${e.target}`)), [graph])
  const degree = useMemo(() => {
    const counts = new Map<string, number>()
    for (const e of graph.edges) {
      counts.set(e.source, (counts.get(e.source) ?? 0) + 1)
      counts.set(e.target, (counts.get(e.target) ?? 0) + 1)
    }
    return counts
  }, [graph])

  const selected = new Set(selectedIds)

  /** Klick auf einen Kopf: auswaehlen. Umschalt+Klick fuegt hinzu oder nimmt weg. */
  function pick(id: string, additive: boolean) {
    if (additive) {
      onSelectionChange(selected.has(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id])
    } else {
      onSelectionChange(selectedIds.length === 1 && selected.has(id) ? [] : [id])
    }
  }

  /** Ein Link zwischen einem geaenderten und einem Kandidaten-Artefakt: der Grund,
   *  warum der Kandidat im Szenario auftaucht. */
  function isImpact(rowId: string, colId: string): boolean {
    const a = highlights[rowId]
    const b = highlights[colId]
    return (a === 'changed' && b === 'candidate') || (a === 'candidate' && b === 'changed')
  }

  return (
    <div>
      <div
        data-testid="matrix"
        className="max-h-[62vh] overflow-auto lg:max-h-[calc(100vh-19.5rem)]"
        onMouseLeave={() => setHover({ row: null, col: null })}
      >
        <table className="border-separate border-spacing-0 text-left">
          <thead>
            <tr>
              <th className="sticky top-0 left-0 z-30 bg-surface px-3 pb-2 align-bottom">
                <span className="eyebrow">Use Cases ↓ · Klassen →</span>
              </th>
              {classes.map((c) => {
                const highlight = highlights[c.id]
                const states = nodeStates(c, highlight)
                return (
                  <th key={c.id} scope="col" className="sticky top-0 z-20 bg-surface p-0 align-bottom">
                    <button
                      data-testid={`col:${c.ref}`}
                      aria-pressed={selected.has(c.id)}
                      title={[c.ref, ...states].join(' · ')}
                      onClick={(e) => pick(c.id, e.shiftKey)}
                      onMouseEnter={() => setHover({ row: null, col: c.id })}
                      className={`flex h-44 w-10 items-end justify-center border-b-2 pb-2 transition ${headerTone(selected.has(c.id), highlight, hover.col === c.id)} ${headerEdge(highlight)}`}
                    >
                      <span className="rotate-180 text-xs leading-4 font-medium whitespace-pre [writing-mode:vertical-rl]">
                        {[c.ref, ...states].join('\n')}
                      </span>
                    </button>
                  </th>
                )
              })}
              <th
                className="sticky top-0 z-20 bg-surface px-2 pb-2 text-center align-bottom"
                title="Anzahl deklarierter Links (Knotengrad). Keine Bewertung."
              >
                <span className="eyebrow">Σ</span>
              </th>
            </tr>
          </thead>

          <tbody>
            {useCases.map((u) => {
              const highlight = highlights[u.id]
              const states = nodeStates(u, highlight)
              return (
                <tr key={u.id}>
                  <th scope="row" className="sticky left-0 z-10 bg-surface p-0 font-normal">
                    <button
                      data-testid={`row:${u.ref}`}
                      aria-pressed={selected.has(u.id)}
                      onClick={(e) => pick(u.id, e.shiftKey)}
                      onMouseEnter={() => setHover({ row: u.id, col: null })}
                      className={`flex h-10 w-80 items-center gap-2 border-l-2 px-3 text-left transition ${headerTone(selected.has(u.id), highlight, hover.row === u.id)} ${headerEdge(highlight)}`}
                    >
                      <span className="font-mono text-xs font-semibold">{u.ref}</span>
                      <span className="min-w-0 flex-1 truncate text-xs">{titleOf(u)}</span>
                      {states.length > 0 && (
                        <span className="shrink-0 rounded-full bg-slate-500/10 px-1.5 py-0.5 text-[0.65rem] font-medium">
                          {states.join(' · ')}
                        </span>
                      )}
                    </button>
                  </th>

                  {classes.map((c) => {
                    const linked = links.has(`${u.id}|${c.id}`)
                    const crosshair = hover.row === u.id || hover.col === c.id
                    const related = selected.has(u.id) || selected.has(c.id)
                    const base = `grid size-10 place-items-center border-r border-b border-slate-200/50 transition ${
                      crosshair ? 'bg-indigo-500/10' : related ? 'bg-indigo-500/[0.04]' : ''
                    }`
                    if (!linked) {
                      return (
                        <td key={c.id} className="p-0">
                          <div className={base} onMouseEnter={() => setHover({ row: u.id, col: c.id })}>
                            <span className="size-1 rounded-full bg-slate-300/70" />
                          </div>
                        </td>
                      )
                    }
                    const impact = isImpact(u.id, c.id)
                    return (
                      <td key={c.id} className="p-0">
                        <button
                          data-testid={`cell:${u.ref}:${c.ref}`}
                          aria-label={`${u.ref} ist ${c.ref} zugeordnet`}
                          title={`${u.ref} → ${c.ref}${impact ? ' (Grund für den Kandidaten)' : ''}`}
                          onClick={() => onSelectionChange([u.id, c.id])}
                          onMouseEnter={() => setHover({ row: u.id, col: c.id })}
                          className={base}
                        >
                          <span
                            className={`size-[1.15rem] rounded-md shadow-sm transition ${
                              impact
                                ? 'bg-amber-500 ring-4 ring-amber-400/30'
                                : related
                                  ? 'bg-indigo-600 ring-4 ring-indigo-500/25'
                                  : 'bg-indigo-500'
                            }`}
                          />
                        </button>
                      </td>
                    )
                  })}

                  <td className="px-2 text-center text-xs text-slate-500 tabular-nums">{degree.get(u.id) ?? 0}</td>
                </tr>
              )
            })}
          </tbody>

          <tfoot>
            <tr>
              <th className="sticky bottom-0 left-0 z-30 bg-surface px-3 py-1.5 text-left">
                <span className="eyebrow">Σ Links je Klasse</span>
              </th>
              {classes.map((c) => (
                <td
                  key={c.id}
                  className="sticky bottom-0 z-20 bg-surface py-1.5 text-center text-xs text-slate-500 tabular-nums"
                >
                  {degree.get(c.id) ?? 0}
                </td>
              ))}
              <td className="sticky bottom-0 z-20 bg-surface" />
            </tr>
          </tfoot>
        </table>
      </div>

      <ul className="flex flex-wrap gap-x-5 gap-y-1 border-t border-slate-200/70 px-4 py-2.5 text-xs text-slate-600">
        <li className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm bg-indigo-500" /> deklarierter Trace-Link
        </li>
        <li className="flex items-center gap-1.5">
          <span className="size-3 rounded-sm bg-amber-500" /> Link zwischen geändertem Artefakt und Kandidat
        </li>
        <li>Leere Zeile oder Spalte: keine Zuordnung, keine Entwarnung</li>
        <li>Σ: Anzahl der Links, keine Bewertung</li>
      </ul>
    </div>
  )
}
