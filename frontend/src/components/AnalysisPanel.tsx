// Ein Szenario im Ueberblick: Auftrag, strukturelle Auswahl, Modellanalyse,
// Entscheidungen, Abdeckung.
//
// Die strukturelle Auswahl (Kandidaten) folgt allein aus den deklarierten
// Trace-Links und ist reproduzierbar. Die Modellanalyse ist ein getrennter,
// nachgelagerter Schritt und ersetzt die Herkunft der Kandidaten nicht
// (CLAUDE.md, Entwurfsregel 1). Beide stehen deshalb in getrennten Abschnitten.

import { useEffect, useState } from 'react'
import { Ban, ExternalLink, Play, RotateCw } from 'lucide-react'
import { api, ApiError } from '../api'
import { formatTime } from '../format'
import { CHANGE_KIND, DIRECTION, SCENARIO_STATE } from '../labels'
import { reportShown } from '../shown'
import { useLoad } from '../useLoad'
import { isBackwardRun } from '../types'
import type { Graph, Scenario, Selection } from '../types'
import { BackwardRunView } from './BackwardRunView'
import { CoveragePanel } from './CoveragePanel'
import { ForwardRunView } from './ForwardRunView'
import { Badge, ErrorBox, Loading, Notice, Section } from './ui'

interface Props {
  baselineId: string
  graph: Graph
  scenario: Scenario
  selection: Selection | null
  /** Der Zustand des Szenarios hat sich geaendert. */
  onScenarioChanged: () => void
}

export function AnalysisPanel({ baselineId, graph, scenario, selection, onScenarioChanged }: Props) {
  const [version, setVersion] = useState(0)
  const [chosenRun, setChosenRun] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [problems, setProblems] = useState<string[] | null>(null)

  const runs = useLoad(() => api.runs(scenario.scenario_id), [scenario.scenario_id, version])
  const decisions = useLoad(() => api.decisions(scenario.scenario_id), [scenario.scenario_id, version])

  const runList = runs.data ?? []
  const run = runList.find((r) => r.run_id === chosenRun) ?? runList[runList.length - 1] ?? null

  // Markierung und Erhaltungskontext werden dem Anwender hier gezeigt:
  // Das gehoert ins Protokoll (Konzept 4.13).
  useEffect(() => {
    if (selection === null) return
    if (selection.direction === 'requirement_to_code') {
      for (const c of selection.candidates) {
        reportShown(scenario.scenario_id, 'marking_shown', c.class_id)
        if (c.preservation_context_ids.length > 0) reportShown(scenario.scenario_id, 'context_shown', c.class_id)
      }
    } else {
      for (const c of selection.candidates) reportShown(scenario.scenario_id, 'marking_shown', c.use_case_id)
    }
  }, [selection, scenario.scenario_id])

  function changed() {
    setVersion((v) => v + 1)
    onScenarioChanged()
  }

  async function startAnalysis() {
    setBusy(true)
    setProblems(null)
    try {
      await api.startAnalysis(scenario.scenario_id)
      setChosenRun(null)
      changed()
    } catch (e) {
      setProblems(e instanceof ApiError ? e.problems : [String(e)])
    } finally {
      setBusy(false)
    }
  }

  async function discard() {
    if (!window.confirm('Szenario verwerfen? Bisherige Ergebnisse bleiben sichtbar, der Ausgangsstand bleibt unverändert.')) return
    try {
      await api.discard(scenario.scenario_id)
      changed()
    } catch (e) {
      setProblems(e instanceof ApiError ? e.problems : [String(e)])
    }
  }

  const canAnalyze = scenario.state === 'structurally_checked' || scenario.state === 'ready_for_review'
  const canDiscard = scenario.state !== 'closed' && scenario.state !== 'discarded'

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-slate-900">{scenario.title}</h3>
          <p className="text-xs text-slate-500">{DIRECTION[scenario.direction]}</p>
        </div>
        <Badge tone="accent">{SCENARIO_STATE[scenario.state]}</Badge>
      </div>

      <Section title="Auftrag">
        <ul className="space-y-2 text-sm">
          {scenario.requirement_changes.map((c, i) => (
            <li key={i} className="rounded-xl border border-slate-200 bg-surface px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="neutral">{CHANGE_KIND[c.kind]}</Badge>
                <code className="font-semibold text-slate-900">{c.use_case_id}</code>
                {c.kind === 'add' && c.manual_class_ids.length > 0 && (
                  <span className="text-xs text-slate-500">Klassen: {c.manual_class_ids.join(', ')}</span>
                )}
              </div>
              {c.target_text && <div className="text-block mt-2">{c.target_text}</div>}
            </li>
          ))}
          {scenario.code_changes.map((c, i) => (
            <li key={i} className="rounded-xl border border-slate-200 bg-surface px-3 py-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="neutral">Codeänderung</Badge>
                <code className="font-semibold text-slate-900">
                  {c.class_id}
                  {c.signature && `#${c.signature.name}(${c.signature.parameter_types.join(', ')})`}
                </code>
              </div>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Strukturelle Auswahl">
        <p className="mb-2 text-xs text-slate-500">
          Herkunft: die deklarierten Trace-Links. Reproduzierbar, keine Bewertung durch ein Modell.
        </p>
        {selection === null ? <Loading /> : <SelectionView selection={selection} />}
      </Section>

      <Section title="Modellanalyse">
        <div className="flex flex-wrap gap-2">
          <button className="btn btn-primary" disabled={busy || !canAnalyze} onClick={startAnalysis}>
            {runList.length > 0 ? <RotateCw className="size-4" aria-hidden /> : <Play className="size-4" aria-hidden />}
            {busy ? 'Analysiere …' : runList.length > 0 ? 'Erneut analysieren' : 'Modellanalyse starten'}
          </button>
          {canDiscard && (
            <button className="btn" onClick={discard}>
              <Ban className="size-4" aria-hidden />
              Szenario verwerfen
            </button>
          )}
        </div>
        <ErrorBox problems={problems} />
        {runs.error && <ErrorBox problems={runs.error} />}

        {runList.length > 1 && (
          <div className="mt-3">
            <label className="field-label" htmlFor="run-select">
              Lauf
            </label>
            <select
              id="run-select"
              className="input"
              value={run?.run_id ?? ''}
              onChange={(e) => setChosenRun(e.target.value)}
            >
              {runList.map((r, i) => (
                <option key={r.run_id} value={r.run_id}>
                  Lauf {i + 1} – {formatTime(r.started_at)}
                </option>
              ))}
            </select>
            <span className="field-hint">Jede Anfrage hat eine eigene Kennung. Frühere Läufe bleiben erhalten.</span>
          </div>
        )}

        <div className="mt-4">
          {run === null && !runs.loading && <p className="text-sm text-slate-500">Noch keine Analyse gestartet.</p>}
          {run !== null && !isBackwardRun(run) && (
            <ForwardRunView
              baselineId={baselineId}
              scenario={scenario}
              run={run}
              decisions={decisions.data?.current ?? []}
              onChanged={changed}
            />
          )}
          {run !== null && isBackwardRun(run) && (
            <BackwardRunView
              baselineId={baselineId}
              graph={graph}
              scenario={scenario}
              run={run}
              decisions={decisions.data?.current ?? []}
              onChanged={changed}
            />
          )}
        </div>
      </Section>

      {run !== null && <CoveragePanel scenario={scenario} version={version} onClosed={changed} />}

      <div className="mt-6 border-t border-slate-200 pt-4">
        <a
          className="btn btn-sm"
          href={api.url(`/api/scenarios/${scenario.scenario_id}/protocol`)}
          target="_blank"
          rel="noreferrer"
        >
          <ExternalLink className="size-3.5" aria-hidden />
          Protokoll dieses Szenarios öffnen (JSON)
        </a>
      </div>
    </div>
  )
}

function SelectionView({ selection }: { selection: Selection }) {
  if (selection.direction === 'requirement_to_code') {
    return (
      <div className="space-y-2">
        {selection.candidates.length === 0 && <p className="text-sm text-slate-500">Keine Kandidatenklassen.</p>}
        {selection.candidates.map((c) => (
          <div key={c.class_id} className="rounded-xl border border-amber-200 bg-amber-50/50 px-3 py-2">
            <div className="flex flex-wrap items-center gap-2">
              <strong className="font-mono text-sm text-slate-900">{c.class_id}</strong>
              {!c.parsed && <Badge tone="error">nicht verarbeitet</Badge>}
            </div>
            <p className="mt-1 text-xs text-slate-600">ausgelöst durch: {c.triggering_use_case_ids.join(', ')}</p>
            <p className="text-xs text-slate-600">
              {c.preservation_context_ids.length > 0 ? (
                <>
                  weiter aktive Use Cases (Erhaltungskontext, nie „betroffen“): {c.preservation_context_ids.join(', ')}
                </>
              ) : (
                <span className="text-slate-500">
                  kein weiterer aktiver Use Case. Das ist keine Freigabe zum Löschen.
                </span>
              )}
            </p>
          </div>
        ))}
        {selection.unresolved.map((u) => (
          <Notice key={u.use_case_id} tone="warn">
            <strong>{u.use_case_id}:</strong> {u.reason}. Eine leere Kandidatenmenge heißt nicht, dass die Änderung
            wirkungslos wäre.
          </Notice>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {selection.candidates.length === 0 && <p className="text-sm text-slate-500">Keine Kandidaten-Use-Cases.</p>}
      {selection.candidates.map((c) => (
        <div key={c.use_case_id} className="rounded-xl border border-amber-200 bg-amber-50/50 px-3 py-2">
          <strong className="text-sm text-slate-900">{c.use_case_id}</strong>
          <p className="mt-1 text-xs text-slate-600">über geänderte Klassen: {c.triggering_class_ids.join(', ')}</p>
        </div>
      ))}
      {selection.unassignable_class_ids.map((id) => (
        <Notice key={id} tone="warn">
          <strong>{id}:</strong> keine deklarierte Zuordnung. Nicht zuordenbar, aber nicht unbeeinträchtigt.
        </Notice>
      ))}
    </div>
  )
}
