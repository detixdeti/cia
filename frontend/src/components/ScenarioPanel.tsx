// Szenarien: bestehende auswaehlen und neue anlegen (F3).
//
// Ein Szenario aendert den Ausgangsstand nie, es verweist nur auf ihn. In der
// Anforderungsrichtung wird ein Use Case deaktiviert, geaendert oder neu
// angelegt. In der Gegenrichtung gibt der Anwender eine geaenderte Fassung von
// Code ein (Konzept 4.3 und 4.7).

import { useState } from 'react'
import { ChevronRight, Plus, Trash2 } from 'lucide-react'
import { api, ApiError } from '../api'
import { signatureText } from '../format'
import { CHANGE_KIND, DIRECTION, SCENARIO_STATE } from '../labels'
import { useLoad } from '../useLoad'
import type { ChangeKind, CodeChangeIn, Direction, Graph, Scenario, ScenarioCreate, Signature } from '../types'
import { Badge, ErrorBox, Loading } from './ui'

interface Props {
  baselineId: string
  graph: Graph
  scenarios: Scenario[]
  currentId: string | null
  onSelect: (scenarioId: string) => void
  onCreated: (scenario: Scenario) => void
}

// Eine Zeile des Formulars in der Anforderungsrichtung.
interface RequirementRow {
  kind: ChangeKind
  useCaseId: string
  text: string
  classIds: string[]
}

// Eine Zeile des Formulars in der Gegenrichtung.
interface CodeRow {
  classId: string
  /** Kennung der gewaehlten Methode. Leer heisst: ganze Klasse. */
  method: string
  signature: Signature | null
  after: string
}

export function ScenarioPanel({ baselineId, graph, scenarios, currentId, onSelect, onCreated }: Props) {
  const [creating, setCreating] = useState(scenarios.length === 0)

  return (
    <div>
      <h3 className="eyebrow mb-2">Szenarien dieses Ausgangsstands</h3>
      {scenarios.length === 0 ? (
        <p className="text-sm text-slate-500">Noch kein Szenario angelegt.</p>
      ) : (
        <ul className="space-y-1.5">
          {scenarios.map((s) => (
            <li key={s.scenario_id}>
              <button
                onClick={() => onSelect(s.scenario_id)}
                className={`flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left transition ${
                  s.scenario_id === currentId
                    ? 'border-indigo-400 bg-indigo-50 ring-1 ring-indigo-200'
                    : 'border-slate-200 bg-surface hover:border-slate-300 hover:bg-slate-50'
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-slate-900">{s.title}</span>
                  <span className="block truncate text-xs text-slate-500">{DIRECTION[s.direction]}</span>
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <Badge tone={s.state === 'discarded' || s.state === 'closed' ? 'muted' : 'accent'}>
                    {SCENARIO_STATE[s.state]}
                  </Badge>
                  <ChevronRight className="size-4 text-slate-400" aria-hidden />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {creating ? (
        <ScenarioForm
          baselineId={baselineId}
          graph={graph}
          onCancel={scenarios.length > 0 ? () => setCreating(false) : null}
          onCreated={(scenario) => {
            setCreating(false)
            onCreated(scenario)
          }}
        />
      ) : (
        <button className="btn btn-primary mt-4" onClick={() => setCreating(true)}>
          <Plus className="size-4" aria-hidden />
          Neues Szenario
        </button>
      )}
    </div>
  )
}

function ScenarioForm({
  baselineId,
  graph,
  onCancel,
  onCreated,
}: {
  baselineId: string
  graph: Graph
  onCancel: (() => void) | null
  onCreated: (scenario: Scenario) => void
}) {
  const useCaseIds = graph.nodes.filter((n) => n.kind === 'use_case').map((n) => n.ref)
  const classIds = graph.nodes.filter((n) => n.kind === 'class').map((n) => n.ref)

  const [title, setTitle] = useState('')
  const [direction, setDirection] = useState<Direction>('requirement_to_code')
  const [requirementRows, setRequirementRows] = useState<RequirementRow[]>([
    { kind: 'deactivate', useCaseId: useCaseIds[0] ?? '', text: '', classIds: [] },
  ])
  const [codeRows, setCodeRows] = useState<CodeRow[]>([
    { classId: classIds[0] ?? '', method: '', signature: null, after: '' },
  ])
  const [busy, setBusy] = useState(false)
  const [problems, setProblems] = useState<string[] | null>(null)

  async function submit() {
    setBusy(true)
    setProblems(null)
    const body: ScenarioCreate =
      direction === 'requirement_to_code'
        ? {
            title: title.trim() || 'Szenario',
            direction,
            requirement_changes: requirementRows.map((r) => ({
              kind: r.kind,
              use_case_id: r.useCaseId.trim(),
              target_text: r.kind === 'deactivate' ? null : r.text,
              manual_class_ids: r.kind === 'add' ? r.classIds : [],
            })),
            code_changes: [],
          }
        : {
            title: title.trim() || 'Szenario',
            direction,
            requirement_changes: [],
            code_changes: codeRows.map((r): CodeChangeIn => ({
              class_id: r.classId,
              after: r.after,
              signature: r.signature,
            })),
          }
    try {
      onCreated(await api.createScenario(baselineId, body))
    } catch (e) {
      setProblems(e instanceof ApiError ? e.problems : [String(e)])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/60 p-4">
      <h4 className="text-sm font-semibold text-slate-900">Neues Szenario</h4>

      <div className="mt-3">
        <label htmlFor="scenario-title" className="field-label">
          Titel
        </label>
        <input
          id="scenario-title"
          data-testid="scenario-title"
          className="input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="z. B. UC5 entfällt"
        />
      </div>

      <fieldset className="mt-4">
        <legend className="field-label">Richtung</legend>
        <div className="grid gap-2">
          {(Object.keys(DIRECTION) as Direction[]).map((d) => (
            <label
              key={d}
              className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-surface px-3 py-2 text-sm text-slate-700 transition hover:border-slate-300 has-[:checked]:border-indigo-400 has-[:checked]:bg-indigo-50 has-[:checked]:text-indigo-900"
            >
              <input
                type="radio"
                name="direction"
                data-testid={d === 'requirement_to_code' ? 'direction-requirement' : 'direction-code'}
                className="size-4 accent-indigo-600"
                checked={direction === d}
                onChange={() => setDirection(d)}
              />
              {DIRECTION[d]}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-4 space-y-3">
        {direction === 'requirement_to_code' ? (
          <>
            {requirementRows.map((row, index) => (
              <RequirementRowForm
                key={index}
                row={row}
                useCaseIds={useCaseIds}
                classIds={classIds}
                onChange={(next) => setRequirementRows(requirementRows.map((r, i) => (i === index ? next : r)))}
                onRemove={
                  requirementRows.length > 1
                    ? () => setRequirementRows(requirementRows.filter((_, i) => i !== index))
                    : null
                }
              />
            ))}
            <button
              className="btn btn-sm"
              onClick={() =>
                setRequirementRows([
                  ...requirementRows,
                  { kind: 'deactivate', useCaseId: useCaseIds[0] ?? '', text: '', classIds: [] },
                ])
              }
            >
              <Plus className="size-3.5" aria-hidden />
              Weitere Änderung
            </button>
          </>
        ) : (
          <>
            {codeRows.map((row, index) => (
              <CodeRowForm
                key={index}
                baselineId={baselineId}
                row={row}
                classIds={classIds}
                onChange={(next) => setCodeRows(codeRows.map((r, i) => (i === index ? next : r)))}
                onRemove={codeRows.length > 1 ? () => setCodeRows(codeRows.filter((_, i) => i !== index)) : null}
              />
            ))}
            <button
              className="btn btn-sm"
              onClick={() =>
                setCodeRows([...codeRows, { classId: classIds[0] ?? '', method: '', signature: null, after: '' }])
              }
            >
              <Plus className="size-3.5" aria-hidden />
              Weitere Codeänderung
            </button>
          </>
        )}
      </div>

      <ErrorBox problems={problems} />
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="btn btn-primary" disabled={busy} onClick={submit}>
          {busy ? 'Lege an …' : 'Szenario anlegen'}
        </button>
        {onCancel && (
          <button className="btn" onClick={onCancel}>
            Abbrechen
          </button>
        )}
      </div>
    </div>
  )
}

function RequirementRowForm({
  row,
  useCaseIds,
  classIds,
  onChange,
  onRemove,
}: {
  row: RequirementRow
  useCaseIds: string[]
  classIds: string[]
  onChange: (row: RequirementRow) => void
  onRemove: (() => void) | null
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <select
          data-testid="requirement-kind"
          aria-label="Art der Änderung"
          className="input w-auto"
          value={row.kind}
          onChange={(e) => onChange({ ...row, kind: e.target.value as ChangeKind })}
        >
          {Object.entries(CHANGE_KIND).map(([kind, label]) => (
            <option key={kind} value={kind}>
              {label}
            </option>
          ))}
        </select>
        {row.kind === 'add' ? (
          <input
            data-testid="requirement-newid"
            aria-label="Neue Kennung"
            className="input w-auto"
            value={row.useCaseId}
            onChange={(e) => onChange({ ...row, useCaseId: e.target.value })}
            placeholder="neue Kennung, z. B. UC7"
          />
        ) : (
          <select
            data-testid="requirement-usecase"
            aria-label="Use Case"
            className="input w-auto"
            value={row.useCaseId}
            onChange={(e) => onChange({ ...row, useCaseId: e.target.value })}
          >
            {useCaseIds.map((id) => (
              <option key={id}>{id}</option>
            ))}
          </select>
        )}
        {onRemove && (
          <button className="btn btn-quiet btn-sm ml-auto" onClick={onRemove} aria-label="Änderung entfernen">
            <Trash2 className="size-3.5" aria-hidden />
            Entfernen
          </button>
        )}
      </div>

      {row.kind !== 'deactivate' && (
        <div className="mt-3">
          <label className="field-label">{row.kind === 'add' ? 'Text des neuen Use Cases' : 'Neuer Text'}</label>
          <textarea
            className="input"
            rows={4}
            value={row.text}
            onChange={(e) => onChange({ ...row, text: e.target.value })}
          />
        </div>
      )}

      {row.kind === 'add' && (
        <div className="mt-3">
          <label className="field-label">Zu untersuchende Klassen (manuelle Zuordnung, Mehrfachauswahl)</label>
          <select
            multiple
            size={5}
            className="input"
            value={row.classIds}
            onChange={(e) => onChange({ ...row, classIds: Array.from(e.target.selectedOptions).map((o) => o.value) })}
          >
            {classIds.map((id) => (
              <option key={id}>{id}</option>
            ))}
          </select>
          <span className="field-hint">
            Ohne Auswahl gibt es keine Kandidaten. Das Werkzeug schlägt hier keine Klassen vor.
          </span>
        </div>
      )}
    </div>
  )
}

function CodeRowForm({
  baselineId,
  row,
  classIds,
  onChange,
  onRemove,
}: {
  baselineId: string
  row: CodeRow
  classIds: string[]
  onChange: (row: CodeRow) => void
  onRemove: (() => void) | null
}) {
  const { data: detail, error, loading } = useLoad(() => api.classDetail(baselineId, row.classId), [baselineId, row.classId])
  const method = detail?.methods.find((m) => signatureText(m.ref.signature) === row.method)
  // Bisherige Fassung: die Methode oder die ganze Klasse, aus dem importierten Stand.
  const before = row.method === '' ? (detail?.source ?? '') : (method?.source ?? '')

  return (
    <div className="rounded-xl border border-slate-200 bg-surface p-3">
      <div className="flex flex-wrap items-center gap-2">
        <select
          data-testid="code-class"
          aria-label="Klasse"
          className="input w-auto"
          value={row.classId}
          onChange={(e) => onChange({ ...row, classId: e.target.value, method: '', signature: null, after: '' })}
        >
          {classIds.map((id) => (
            <option key={id}>{id}</option>
          ))}
        </select>
        <select
          data-testid="code-method"
          aria-label="Methode"
          className="input w-auto max-w-full"
          value={row.method}
          onChange={(e) => {
            const chosen = detail?.methods.find((m) => signatureText(m.ref.signature) === e.target.value)
            onChange({ ...row, method: e.target.value, signature: chosen?.ref.signature ?? null, after: '' })
          }}
        >
          <option value="">ganze Klasse</option>
          {detail?.methods.map((m) => {
            const text = signatureText(m.ref.signature)
            return (
              <option key={text + m.ref.source_range.start_byte} value={text}>
                {text}
              </option>
            )
          })}
        </select>
        {onRemove && (
          <button className="btn btn-quiet btn-sm ml-auto" onClick={onRemove} aria-label="Codeänderung entfernen">
            <Trash2 className="size-3.5" aria-hidden />
            Entfernen
          </button>
        )}
      </div>

      <ErrorBox problems={error} />
      {loading && <Loading />}

      <div className="mt-3">
        <label className="field-label">Bisherige Fassung (aus dem importierten Stand)</label>
        <textarea rows={6} readOnly value={before} className="input font-mono text-xs" data-testid="code-before" />
      </div>
      <div className="mt-3">
        <label className="field-label">Geänderte Fassung</label>
        <textarea
          rows={6}
          value={row.after}
          className="input font-mono text-xs"
          data-testid="code-after"
          onChange={(e) => onChange({ ...row, after: e.target.value })}
        />
        <button
          className="btn btn-sm mt-2"
          data-testid="code-take-over"
          onClick={() => onChange({ ...row, after: before })}
          disabled={before === ''}
        >
          Bisherige Fassung als Ausgangspunkt übernehmen
        </button>
      </div>
    </div>
  )
}
