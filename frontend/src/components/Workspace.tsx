// Der Arbeitsbereich zu einem Ausgangsstand: links der Graph, rechts drei
// Reiter (Auswahl, Szenario, Analyse).

import { useMemo, useState } from 'react'
import {
  Activity,
  ClipboardList,
  FileCode,
  FileText,
  Grid3x3,
  Layers,
  Link2,
  MousePointerClick,
  Network,
  type LucideIcon,
} from 'lucide-react'
import { api } from '../api'
import { isUseCaseNode, refOf } from '../format'
import type { Highlight } from '../graphLayout'
import { useLoad } from '../useLoad'
import type { Graph, Scenario, Selection } from '../types'
import { AnalysisPanel } from './AnalysisPanel'
import { DetailPanel } from './DetailPanel'
import { GraphView } from './GraphView'
import { Matrix } from './Matrix'
import { ImportReport } from './ImportReport'
import { ScenarioPanel } from './ScenarioPanel'
import { Badge, ErrorBox, Loading } from './ui'

type Tab = 'auswahl' | 'szenario' | 'analyse'
type View = 'graph' | 'matrix'

const TABS: { id: Tab; label: string; icon: LucideIcon }[] = [
  { id: 'auswahl', label: 'Auswahl', icon: MousePointerClick },
  { id: 'szenario', label: 'Szenario', icon: Layers },
  { id: 'analyse', label: 'Analyse', icon: Activity },
]

/** Umschalter zwischen den beiden Darstellungen derselben Relation. */
function ViewSwitch({ view, onChange }: { view: View; onChange: (view: View) => void }) {
  const options: { id: View; label: string; icon: LucideIcon }[] = [
    { id: 'graph', label: 'Graph', icon: Network },
    { id: 'matrix', label: 'Matrix', icon: Grid3x3 },
  ]
  return (
    <div role="group" aria-label="Darstellung" className="inline-flex gap-1 rounded-xl bg-slate-100 p-1">
      {options.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          data-testid={`view-${id}`}
          aria-pressed={view === id}
          onClick={() => onChange(id)}
          className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
            view === id
              ? 'bg-surface text-indigo-700 shadow-sm ring-1 ring-slate-200/80'
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          <Icon className="size-4" aria-hidden />
          {label}
        </button>
      ))}
    </div>
  )
}

/** Eine Kennzahl als kleines Etikett. */
function Stat({ icon: Icon, value, label }: { icon: LucideIcon; value: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200/80 bg-surface/70 px-3 py-1 text-xs text-slate-600 backdrop-blur">
      <Icon className="size-3.5 text-slate-400" aria-hidden />
      <strong className="font-semibold text-slate-900 tabular-nums">{value}</strong> {label}
    </span>
  )
}

export function Workspace({ baselineId }: { baselineId: string }) {
  const graph = useLoad(() => api.graph(baselineId), [baselineId])
  const report = useLoad(() => api.baseline(baselineId), [baselineId])
  const scenarios = useLoad(() => api.scenarios(baselineId), [baselineId])

  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [onlySubgraph, setOnlySubgraph] = useState(false)
  const [tab, setTab] = useState<Tab>('auswahl')
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [showReport, setShowReport] = useState(false)
  const [view, setView] = useState<View>('graph')

  // Teilgraph der Auswahl (F2): die direkten Nachbarn, nicht weiter.
  const subgraph = useLoad<Graph | null>(
    () =>
      selectedIds.length === 0
        ? Promise.resolve(null)
        : api.subgraph(
            baselineId,
            selectedIds.filter(isUseCaseNode).map(refOf),
            selectedIds.filter((id) => !isUseCaseNode(id)).map(refOf),
          ),
    [baselineId, selectedIds.join('|')],
  )

  // Strukturelle Auswahl des aktuellen Szenarios.
  const selection = useLoad<Selection | null>(
    () => (currentId === null ? Promise.resolve(null) : api.selection(currentId)),
    [currentId],
  )

  const current: Scenario | null = scenarios.data?.find((s) => s.scenario_id === currentId) ?? null

  // Markierungen im Graphen: Szenario zuerst, dann Nachbarn der Auswahl.
  const highlights = useMemo(() => {
    const result: Record<string, Highlight> = {}
    const sel = selection.data
    if (sel?.direction === 'requirement_to_code') {
      sel.candidates.forEach((c) => (result[`class:${c.class_id}`] = 'candidate'))
      sel.changed_use_case_ids.forEach((id) => (result[`uc:${id}`] = 'changed'))
    } else if (sel) {
      sel.candidates.forEach((c) => (result[`uc:${c.use_case_id}`] = 'candidate'))
      sel.changed_class_ids.forEach((id) => (result[`class:${id}`] = 'changed'))
    }
    subgraph.data?.nodes.forEach((n) => {
      if (n.selected === false && !result[n.id]) result[n.id] = 'neighbor'
    })
    return result
  }, [selection.data, subgraph.data])

  const visibleIds = useMemo(
    () => (onlySubgraph && subgraph.data ? new Set(subgraph.data.nodes.map((n) => n.id)) : null),
    [onlySubgraph, subgraph.data],
  )

  function selectScenario(id: string) {
    setCurrentId(id)
    setTab('analyse')
  }

  const counts = report.data?.counts

  return (
    <div className="reveal space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <h2 className="mr-1 text-xl font-semibold tracking-tight text-slate-900">{report.data?.label ?? '…'}</h2>
          {counts && (
            <>
              <Stat icon={FileText} value={counts.use_cases} label="Use Cases" />
              <Stat icon={FileCode} value={counts.classes} label="Klassen" />
              <Stat icon={Link2} value={counts.trace_links} label="Trace-Links" />
            </>
          )}
          {report.data?.has_errors && <Badge tone="error">Import mit Fehlern</Badge>}
        </div>
        <button className="btn btn-sm" onClick={() => setShowReport(!showReport)}>
          <ClipboardList className="size-3.5" aria-hidden />
          Import-Bericht {showReport ? 'ausblenden' : 'anzeigen'}
        </button>
      </div>

      {showReport && report.data && (
        <div className="card reveal max-h-[45vh] overflow-auto p-6">
          <ImportReport report={report.data} />
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(420px,560px)]">
        <div className="card self-start overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/70 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold tracking-tight text-slate-900">Zuordnungen</h2>
              <p className="text-xs text-slate-500">
                {view === 'graph'
                  ? 'Klick wählt aus, Umschalt+Klick mehrere. Die Anordnung hat keine Bedeutung.'
                  : 'Zeilen sind Use Cases, Spalten Klassen. Ein Punkt ist ein deklarierter Link.'}
              </p>
            </div>
            <ViewSwitch view={view} onChange={setView} />
          </div>
          <ErrorBox problems={graph.error} />
          {graph.data ? (
            view === 'graph' ? (
              <GraphView
                graph={graph.data}
                highlights={highlights}
                visibleIds={visibleIds}
                initialSelection={selectedIds}
                onSelectionChange={setSelectedIds}
              />
            ) : (
              <Matrix
                graph={graph.data}
                selectedIds={selectedIds}
                highlights={highlights}
                visibleIds={visibleIds}
                onSelectionChange={setSelectedIds}
              />
            )
          ) : (
            !graph.error && (
              <div className="p-6">
                <Loading what="Lade Graph" />
              </div>
            )
          )}
        </div>

        <aside className="card flex flex-col overflow-hidden lg:sticky lg:top-[5.25rem] lg:max-h-[calc(100vh-6.75rem)]">
          <nav aria-label="Bereiche" className="m-3 mb-0 flex gap-1 rounded-xl bg-slate-100 p-1">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  id === tab
                    ? 'bg-surface text-indigo-700 shadow-sm ring-1 ring-slate-200/80'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                <Icon className="size-4" aria-hidden />
                {label}
              </button>
            ))}
          </nav>

          <div data-testid="tab-body" className="flex-1 overflow-y-auto p-5">
            <div key={tab} className="reveal">
              {tab === 'auswahl' && (
                <DetailPanel
                  baselineId={baselineId}
                  selectedIds={selectedIds}
                  subgraph={subgraph.data}
                  onlySubgraph={onlySubgraph}
                  onToggleOnlySubgraph={setOnlySubgraph}
                />
              )}

              {tab === 'szenario' && graph.data && (
                <ScenarioPanel
                  baselineId={baselineId}
                  graph={graph.data}
                  scenarios={scenarios.data ?? []}
                  currentId={currentId}
                  onSelect={selectScenario}
                  onCreated={(scenario) => {
                    scenarios.reload()
                    selectScenario(scenario.scenario_id)
                  }}
                />
              )}

              {tab === 'analyse' &&
                (currentId === null ? (
                  <p className="text-sm text-slate-500">
                    Wählen Sie im Reiter „Szenario“ ein Szenario aus oder legen Sie eines an.
                  </p>
                ) : current === null || graph.data === null ? (
                  <Loading />
                ) : (
                  <AnalysisPanel
                    baselineId={baselineId}
                    graph={graph.data}
                    scenario={current}
                    selection={selection.data}
                    onScenarioChanged={scenarios.reload}
                  />
                ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
