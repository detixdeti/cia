// Ergebnis eines Analyselaufs in der Gegenrichtung (F6): Codeaenderung gegen
// die verknuepften Use Cases.
//
// Konzept 4.7: Eine Abweichung kann heissen, dass der Code falsch ist. Ein
// geaenderter Anforderungstext ist nie die bevorzugte Loesung. "Annehmen"
// heisst hier: Die Codeaenderung ist gewollt, der Textvorschlag wird
// uebernommen. "Verwerfen" heisst: Die Anforderung gilt weiter, der Code ist zu
// pruefen.

import { useState } from 'react'
import { Columns2 } from 'lucide-react'
import { api } from '../api'
import { ANSWER_STATE, DEVIATION_STATUS, PROBLEM } from '../labels'
import { reportShown } from '../shown'
import { useLoad } from '../useLoad'
import type { BackwardRun, Decision, DeviationStatus, Graph, Scenario, UseCaseAnalysis } from '../types'
import { Comparison } from './Comparison'
import { DecisionControls } from './DecisionControls'
import { Badge, Notice, type Tone } from './ui'

interface Props {
  baselineId: string
  graph: Graph
  scenario: Scenario
  run: BackwardRun
  decisions: Decision[]
  onChanged: () => void
}

const STATUS_TONE: Record<DeviationStatus, Tone> = {
  possible_deviation: 'warn',
  no_deviation_visible: 'muted',
  insufficient_information: 'warn',
}

export function BackwardRunView({ baselineId, graph, scenario, run, decisions, onChanged }: Props) {
  return (
    <div className="space-y-4">
      <Notice tone="info">
        Eine mögliche Abweichung kann heißen, dass der <strong>Code</strong> falsch ist. Ob die Änderung fachlich
        gewollt ist, entscheiden Sie. Ein geänderter Anforderungstext ist nicht die bevorzugte Lösung.
      </Notice>

      {run.unassignable_class_ids.map((id) => (
        <Notice key={id} tone="warn">
          <strong>{id}</strong> hat keine deklarierte Zuordnung: nicht zuordenbar, aber nicht unbeeinträchtigt.
        </Notice>
      ))}
      {run.results.length === 0 && run.unassignable_class_ids.length === 0 && (
        <p className="text-sm text-slate-500">Keine Kandidaten.</p>
      )}

      {run.results.map((result) => (
        <UseCaseCard
          key={result.use_case_id}
          baselineId={baselineId}
          title={graph.nodes.find((n) => n.id === `uc:${result.use_case_id}`)?.label ?? result.use_case_id}
          scenario={scenario}
          run={run}
          result={result}
          decision={decisions.find((d) => d.run_id === run.run_id && d.subject_id === result.use_case_id)}
          onChanged={onChanged}
        />
      ))}
    </div>
  )
}

function UseCaseCard({
  baselineId,
  title,
  scenario,
  run,
  result,
  decision,
  onChanged,
}: {
  baselineId: string
  title: string
  scenario: Scenario
  run: BackwardRun
  result: UseCaseAnalysis
  decision: Decision | undefined
  onChanged: () => void
}) {
  const [comparing, setComparing] = useState(false)
  const useCase = useLoad(() => api.useCase(baselineId, result.use_case_id), [baselineId, result.use_case_id])
  const { answer } = result
  const assessment = answer.assessment

  const blockers = [
    ...answer.assessment_problems.map((p) => PROBLEM[p] ?? p),
    ...(assessment?.proposed_text ? [] : [PROBLEM.no_proposed_text]),
  ]

  function toggleComparison() {
    if (!comparing) reportShown(scenario.scenario_id, 'comparison_shown', result.use_case_id)
    setComparing(!comparing)
  }

  return (
    <article className="card overflow-hidden">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-4 py-2.5">
        <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
        {assessment === null ? (
          <Badge tone="warn">{ANSWER_STATE[answer.state]}</Badge>
        ) : (
          <Badge tone={STATUS_TONE[assessment.status]}>{DEVIATION_STATUS[assessment.status]}</Badge>
        )}
      </header>

      <div className="space-y-3 p-4">
        {assessment === null && (
          <Notice tone="warn">
            <strong>{ANSWER_STATE[answer.state]}.</strong> {answer.problems.join('; ')} Dieser Use Case bleibt offen.
            Das ist keine Entwarnung.
          </Notice>
        )}

        {assessment !== null && (
          <>
            {answer.assessment_problems.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {answer.assessment_problems.map((p) => (
                  <Badge key={p} tone="error">
                    {PROBLEM[p] ?? p}
                  </Badge>
                ))}
              </div>
            )}
            <p className="text-xs text-slate-500">Aussage des Modells „{result.provider_name}“, fachlich ungeprüft.</p>

            <div className="space-y-1 text-sm text-slate-700">
              {assessment.affected_passage && (
                <p>
                  <span className="font-medium text-slate-900">Betroffene Stelle im Use Case:</span>{' '}
                  {assessment.affected_passage}
                </p>
              )}
              {assessment.reason && (
                <p>
                  <span className="font-medium text-slate-900">Begründung (Aussage des Modells):</span>{' '}
                  {assessment.reason}
                </p>
              )}
              {assessment.status === 'no_deviation_visible' && (
                <p className="text-xs text-slate-500">
                  Das ist nur „im betrachteten Kontext nicht erkennbar“, keine Garantie, dass der Use Case erfüllt
                  bleibt.
                </p>
              )}
            </div>

            {assessment.status === 'possible_deviation' && (
              <div>
                {assessment.proposed_text && (
                  <>
                    <button className="btn btn-sm" onClick={toggleComparison}>
                      <Columns2 className="size-3.5" aria-hidden />
                      {comparing ? 'Vergleich ausblenden' : 'Bisheriger und vorgeschlagener Text vergleichen'}
                    </button>
                    {comparing && (
                      <Comparison
                        beforeTitle="Bisheriger Use-Case-Text"
                        afterTitle="Vorgeschlagener Text (ungeprüft)"
                        before={useCase.data?.text ?? '(Text wird geladen …)'}
                        after={assessment.proposed_text}
                      />
                    )}
                  </>
                )}
                <DecisionControls
                  scenarioId={scenario.scenario_id}
                  runId={run.run_id}
                  subjectId={result.use_case_id}
                  entryIndex={0}
                  current={decision}
                  blockers={blockers}
                  enabled={scenario.state === 'ready_for_review'}
                  acceptLabel="Änderung ist gewollt: Textvorschlag übernehmen"
                  rejectLabel="Anforderung gilt weiter: Code prüfen"
                  onDecided={onChanged}
                />
              </div>
            )}

            {answer.assumptions.length > 0 && (
              <p className="text-sm text-slate-600">
                <span className="font-medium text-slate-700">Annahmen des Modells:</span> {answer.assumptions.join('; ')}
              </p>
            )}
            {answer.missing_context.length > 0 && (
              <p className="text-sm text-slate-600">
                <span className="font-medium text-slate-700">Fehlender Kontext laut Modell:</span>{' '}
                {answer.missing_context.join('; ')}
              </p>
            )}
          </>
        )}

        <details className="disclosure">
          <summary>Eingabe und Rohantwort (wie im Protokoll)</summary>
          <p className="text-xs text-slate-500">
            Vorlage {result.prompt_version}. Anfrage: {result.requested_at}.
          </p>
          <pre className="code-block">{result.prompt}</pre>
          <pre className="code-block">{result.raw_response ?? '(keine Antwort erhalten)'}</pre>
        </details>
      </div>
    </article>
  )
}
