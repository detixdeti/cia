// Zugriff auf das Backend. Jede Funktion entspricht einem Endpunkt.

import type {
  BaselineDetail,
  BaselineSummary,
  ClassDetail,
  Closure,
  CoverageResponse,
  Decision,
  DecisionKind,
  Decisions,
  Graph,
  Info,
  Run,
  Scenario,
  ScenarioCreate,
  Selection,
  UiEventType,
  UseCaseDetail,
} from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/** Ein Fehler des Backends mit Statuscode und Meldung(en). */
export class ApiError extends Error {
  status: number
  problems: string[]

  constructor(status: number, problems: string[]) {
    super(problems.join('; '))
    this.status = status
    this.problems = problems
  }
}

/** Macht aus dem "detail" des Backends eine Liste lesbarer Meldungen. */
function toProblems(detail: unknown): string[] {
  if (typeof detail === 'string') return [detail]
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === 'string' ? d : JSON.stringify(d)))
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return [String((detail as { message: unknown }).message)]
  }
  return ['Unbekannter Fehler']
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new ApiError(0, [`Das Backend unter ${API} ist nicht erreichbar`])
  }

  if (!response.ok) {
    let detail: unknown = response.statusText
    try {
      detail = ((await response.json()) as { detail?: unknown }).detail
    } catch {
      // Die Antwort war kein JSON, der Statustext genuegt.
    }
    throw new ApiError(response.status, toProblems(detail))
  }
  return (await response.json()) as T
}

function post<T>(path: string, body: unknown = {}): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

export interface UploadedFile {
  path: string
  content: string
}

export interface UploadBody {
  label: string
  use_cases: UploadedFile[]
  sources: UploadedFile[]
  trace_links: UploadedFile | null
}

export const api = {
  /** Adresse fuer Links, die der Browser direkt oeffnet (z. B. das Protokoll). */
  url: (path: string) => `${API}${path}`,

  info: () => request<Info>('/api/info'),

  baselines: () => request<BaselineSummary[]>('/api/baselines'),
  baseline: (id: string) => request<BaselineDetail>(`/api/baselines/${id}`),
  upload: (body: UploadBody) => post<BaselineDetail>('/api/baselines/upload', body),
  graph: (id: string) => request<Graph>(`/api/baselines/${id}/graph`),
  subgraph: (id: string, useCases: string[], classes: string[]) => {
    const query = [
      ...useCases.map((u) => `use_case=${encodeURIComponent(u)}`),
      ...classes.map((c) => `class=${encodeURIComponent(c)}`),
    ].join('&')
    return request<Graph>(`/api/baselines/${id}/subgraph?${query}`)
  },
  useCase: (baselineId: string, id: string) =>
    request<UseCaseDetail>(`/api/baselines/${baselineId}/use-cases/${encodeURIComponent(id)}`),
  classDetail: (baselineId: string, id: string) =>
    request<ClassDetail>(`/api/baselines/${baselineId}/classes/${encodeURIComponent(id)}`),

  scenarios: (baselineId: string) => request<Scenario[]>(`/api/baselines/${baselineId}/scenarios`),
  createScenario: (baselineId: string, body: ScenarioCreate) =>
    post<Scenario>(`/api/baselines/${baselineId}/scenarios`, body),
  scenario: (id: string) => request<Scenario>(`/api/scenarios/${id}`),
  selection: (id: string) => request<Selection>(`/api/scenarios/${id}/selection`),
  discard: (id: string) => post<Scenario>(`/api/scenarios/${id}/discard`),

  startAnalysis: (id: string) => post<Run>(`/api/scenarios/${id}/analyses`),
  runs: (id: string) => request<Run[]>(`/api/scenarios/${id}/analyses`),

  decisions: (id: string) => request<Decisions>(`/api/scenarios/${id}/decisions`),
  decide: (
    id: string,
    body: {
      run_id: string
      subject_id: string
      entry_index: number
      kind: DecisionKind
      revised_proposal?: string
    },
  ) => post<Decision>(`/api/scenarios/${id}/decisions`, body),

  coverage: (id: string) => request<CoverageResponse>(`/api/scenarios/${id}/coverage`),
  close: (id: string, body: { acknowledge_open_items: boolean; note: string | null }) =>
    post<Closure>(`/api/scenarios/${id}/close`, body),

  /** Meldet, was die Oberflaeche angezeigt hat (Konzept 4.13). */
  event: (id: string, type: UiEventType, subjectId: string) =>
    post<unknown>(`/api/scenarios/${id}/events`, { type, subject_id: subjectId }),
}
