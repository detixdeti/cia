// Ergebnis eines Analyselaufs in der Anforderungsrichtung (F4 und F5).
//
// Je Kandidatenklasse: Aussagen des Modells zu einzelnen Methoden, mit
// Ist-Soll-Vergleich und Entscheidung. Alles, was das Modell sagt, ist als
// Aussage des Modells gekennzeichnet und fachlich ungeprueft (Konzept 4.6).
// Was offen bleibt, steht offen da: Eine nicht genannte Methode gilt nicht als
// unveraendert, ein Fehler ist keine Entwarnung (Konzept 4.5 und 4.10).

import { useState } from 'react'
import { Columns2 } from 'lucide-react'
import { api } from '../api'
import { signatureText } from '../format'
import { ANSWER_STATE, ENTRY_STATUS, PROBLEM } from '../labels'
import { reportShown } from '../shown'
import { useLoad } from '../useLoad'
import type { CheckedEntry, ClassDetail, ClassResult, Decision, EntryStatus, ForwardRun, Scenario } from '../types'
import { Comparison } from './Comparison'
import { DecisionControls } from './DecisionControls'
import { Badge, Notice, type Tone } from './ui'

interface Props {
  baselineId: string
  scenario: Scenario
  run: ForwardRun
  /** Die jeweils letzten Entscheidungen des Szenarios. */
  decisions: Decision[]
  onChanged: () => void
}

const STATUS_TONE: Record<EntryStatus, Tone> = {
  change_proposed: 'warn',
  no_change_visible: 'muted',
  not_assessable: 'warn',
}

/** Farbiger Rand links: hilft beim Ueberfliegen, ersetzt aber nie die Beschriftung. */
const STATUS_ACCENT: Record<EntryStatus, string> = {
  change_proposed: 'border-l-amber-400',
  no_change_visible: 'border-l-slate-300',
  not_assessable: 'border-l-amber-200',
}

export function ForwardRunView({ baselineId, scenario, run, decisions, onChanged }: Props) {
  return (
    <div className="space-y-4">
      {run.results.length === 0 && (
        <p className="text-sm text-slate-500">
          Keine Kandidatenklassen. Das ist keine Aussage, dass die Änderung wirkungslos wäre.
        </p>
      )}
      {run.results.map((result) => (
        <ClassResultCard
          key={result.class_id}
          baselineId={baselineId}
          scenario={scenario}
          run={run}
          result={result}
          decisions={decisions.filter((d) => d.run_id === run.run_id && d.subject_id === result.class_id)}
          onChanged={onChanged}
        />
      ))}
    </div>
  )
}

function ClassResultCard({
  baselineId,
  scenario,
  run,
  result,
  decisions,
  onChanged,
}: {
  baselineId: string
  scenario: Scenario
  run: ForwardRun
  result: ClassResult
  decisions: Decision[]
  onChanged: () => void
}) {
  const detail = useLoad(() => api.classDetail(baselineId, result.class_id), [baselineId, result.class_id])
  const analysis = result.analysis

  return (
    <article className="card overflow-hidden">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-slate-50 px-4 py-2.5">
        <h4 className="font-mono text-sm font-semibold text-slate-900">{result.class_id}</h4>
        {analysis === null ? (
          <Badge tone="warn">nicht verarbeitet</Badge>
        ) : (
          <Badge tone={analysis.answer.state === 'answered' ? 'neutral' : 'warn'}>
            {ANSWER_STATE[analysis.answer.state]}
          </Badge>
        )}
      </header>

      <div className="space-y-3 p-4">
        {analysis === null && (
          <Notice tone="warn">
            <strong>Nicht verarbeitet:</strong> {result.not_processed_reason}. Diese Klasse ist nicht als unauffällig zu
            lesen. Das Modell wurde nicht gefragt.
          </Notice>
        )}

        {analysis !== null && analysis.answer.state !== 'answered' && (
          <Notice tone="warn">
            <strong>{ANSWER_STATE[analysis.answer.state]}.</strong> {analysis.answer.problems.join('; ')} Alle Methoden
            dieser Klasse bleiben offen. Das ist keine Entwarnung.
          </Notice>
        )}

        {analysis !== null && analysis.answer.state === 'answered' && (
          <>
            <p className="text-xs text-slate-500">Aussagen des Modells „{analysis.provider_name}“, fachlich ungeprüft.</p>
            {analysis.answer.entries.map((checked, index) => (
              <EntryCard
                key={index}
                scenario={scenario}
                runId={run.run_id}
                classId={result.class_id}
                index={index}
                checked={checked}
                detail={detail.data}
                decision={decisions.find((d) => d.entry_index === index)}
                onChanged={onChanged}
              />
            ))}

            {analysis.answer.unanswered_methods.length > 0 && (
              <details className="disclosure">
                <summary>
                  Zu {analysis.answer.unanswered_methods.length} Methoden sagt das Modell nichts. Sie bleiben offen und
                  gelten nicht als unverändert.
                </summary>
                <ul className="list-disc space-y-0.5 pl-4 text-sm text-slate-700">
                  {analysis.answer.unanswered_methods.map((m) => (
                    <li key={signatureText(m.signature) + m.source_range.start_byte}>
                      <code>{signatureText(m.signature)}</code>
                    </li>
                  ))}
                </ul>
              </details>
            )}

            {analysis.answer.assumptions.length > 0 && (
              <div className="text-sm">
                <p className="font-medium text-slate-700">Annahmen des Modells</p>
                <ul className="list-disc pl-5 text-slate-600">
                  {analysis.answer.assumptions.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
            {analysis.answer.missing_context.length > 0 && (
              <div className="text-sm">
                <p className="font-medium text-slate-700">Fehlender Kontext laut Modell</p>
                <ul className="list-disc pl-5 text-slate-600">
                  {analysis.answer.missing_context.map((a, i) => (
                    <li key={i}>{a}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {analysis !== null && (
          <details className="disclosure">
            <summary>Eingabe und Rohantwort (wie im Protokoll)</summary>
            <p className="text-xs text-slate-500">
              Vorlage {analysis.prompt_version}. Anfrage: {analysis.requested_at}.
            </p>
            <pre className="code-block">{analysis.prompt}</pre>
            <pre className="code-block">{analysis.raw_response ?? '(keine Antwort erhalten)'}</pre>
          </details>
        )}
      </div>
    </article>
  )
}

function EntryCard({
  scenario,
  runId,
  classId,
  index,
  checked,
  detail,
  decision,
  onChanged,
}: {
  scenario: Scenario
  runId: string
  classId: string
  index: number
  checked: CheckedEntry
  detail: ClassDetail | null
  decision: Decision | undefined
  onChanged: () => void
}) {
  const [comparing, setComparing] = useState(false)
  const { entry } = checked
  const blockers = checked.problems.map((p) => PROBLEM[p] ?? p)

  function istText(): string {
    if (checked.method_ref === null) {
      return entry.target_kind === 'new_method'
        ? '(neue Methode, es gibt noch keinen Quelltext)'
        : '(kein bestehender Quelltext)'
    }
    const wanted = signatureText(checked.method_ref.signature)
    return detail?.methods.find((m) => signatureText(m.ref.signature) === wanted)?.source ?? '(Quelltext wird geladen …)'
  }

  function toggleComparison() {
    if (!comparing) reportShown(scenario.scenario_id, 'comparison_shown', `${classId}#${entry.target}`)
    setComparing(!comparing)
  }

  return (
    <div className={`rounded-xl border border-l-4 border-slate-200 bg-surface p-3 ${STATUS_ACCENT[entry.status]}`}>
      <div className="flex flex-wrap items-center gap-1.5">
        <code className="font-semibold text-slate-900">{entry.target}</code>
        {entry.target_kind === 'new_method' && <Badge tone="info">neue Methode</Badge>}
        {entry.target_kind === 'class' && <Badge tone="info">Klassenstelle</Badge>}
        <Badge tone={STATUS_TONE[entry.status]}>{ENTRY_STATUS[entry.status]}</Badge>
        {checked.problems.map((p) => (
          <Badge key={p} tone="error">
            {PROBLEM[p] ?? p}
          </Badge>
        ))}
      </div>

      <div className="mt-2 space-y-1 text-sm text-slate-700">
        {entry.use_case_passage && (
          <p>
            <span className="font-medium text-slate-900">Betroffene Stelle im Use Case:</span> {entry.use_case_passage}
          </p>
        )}
        {entry.reason && (
          <p>
            <span className="font-medium text-slate-900">Begründung (Aussage des Modells):</span> {entry.reason}
          </p>
        )}
        {entry.status === 'no_change_visible' && (
          <p className="text-xs text-slate-500">Das ist nur „im betrachteten Kontext nicht erkennbar“, keine Garantie.</p>
        )}
      </div>

      {entry.status === 'change_proposed' && (
        <>
          <button className="btn btn-sm mt-3" onClick={toggleComparison}>
            <Columns2 className="size-3.5" aria-hidden />
            {comparing ? 'Vergleich ausblenden' : 'Ist-Soll-Vergleich anzeigen'}
          </button>
          {comparing && (
            <Comparison
              beforeTitle="Ist (importierter Stand)"
              afterTitle="Soll (Vorschlag des Modells, ungeprüft)"
              before={istText()}
              after={entry.proposal ?? ''}
            />
          )}
          <DecisionControls
            scenarioId={scenario.scenario_id}
            runId={runId}
            subjectId={classId}
            entryIndex={index}
            current={decision}
            blockers={blockers}
            enabled={scenario.state === 'ready_for_review'}
            acceptLabel="Vorschlag annehmen"
            rejectLabel="Vorschlag verwerfen"
            onDecided={onChanged}
          />
        </>
      )}
    </div>
  )
}
