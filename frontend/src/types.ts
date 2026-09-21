// Formen der Antworten des Backends. Die Namen entsprechen den JSON-Feldern.

export type Severity = 'error' | 'warning' | 'info'

export interface Diagnostic {
  code: string
  severity: Severity
  message: string
  source_file: string | null
  line_number: number | null
}

export interface BaselineSummary {
  baseline_id: string
  label: string
  counts: Record<string, number>
  diagnostics: Record<string, number>
  has_errors: boolean
}

export interface BaselineDetail extends BaselineSummary {
  diagnostic_entries: Diagnostic[]
}

export interface Info {
  provider: string
  settings: Record<string, string | number>
}

// --- Graph ---------------------------------------------------------------

export interface GraphNode {
  id: string
  kind: 'use_case' | 'class'
  ref: string
  label: string
  linked: boolean
  selected: boolean | null
  active: boolean | null
  parsed: boolean | null
  method_count: number | null
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  origin: 'imported' | 'scenario'
}

export interface Graph {
  baseline_id: string
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// --- Artefakte -----------------------------------------------------------

export interface Signature {
  name: string
  parameter_types: string[]
}

export interface MethodRef {
  baseline_id: string
  class_id: string
  signature: Signature
  source_range: { start_line: number; end_line: number; start_byte: number; end_byte: number }
}

export interface MethodInfo {
  ref: MethodRef
  is_constructor: boolean
  source: string
}

export interface ClassDetail {
  id: string
  file_name: string
  relative_path: string
  source: string
  parsed: boolean
  parse_error: string | null
  methods: MethodInfo[]
  use_case_ids: string[]
  linked: boolean
}

export interface UseCaseDetail {
  id: string
  title: string
  text: string
  source_file: string | null
  active: boolean
  class_ids: string[]
  linked: boolean
}

// --- Szenarien -----------------------------------------------------------

export type Direction = 'requirement_to_code' | 'code_to_requirement'

export type ScenarioState =
  | 'created'
  | 'structurally_checked'
  | 'analysis_running'
  | 'ready_for_review'
  | 'closed'
  | 'discarded'

export type ChangeKind = 'deactivate' | 'modify' | 'add'

export interface RequirementChange {
  kind: ChangeKind
  use_case_id: string
  target_text: string | null
  manual_class_ids: string[]
}

export interface CodeChangeIn {
  class_id: string
  after: string
  signature: Signature | null
}

export interface CodeChangeOut {
  class_id: string
  before: string
  after: string
  signature: Signature | null
}

export interface ScenarioCreate {
  title: string
  direction: Direction
  requirement_changes: RequirementChange[]
  code_changes: CodeChangeIn[]
}

export interface Scenario {
  scenario_id: string
  baseline_id: string
  title: string
  direction: Direction
  state: ScenarioState
  created_at: string
  requirement_changes: RequirementChange[]
  code_changes: CodeChangeOut[]
}

// --- Strukturelle Auswahl -------------------------------------------------

export interface ClassCandidate {
  class_id: string
  triggering_use_case_ids: string[]
  preservation_context_ids: string[]
  parsed: boolean
}

export interface ForwardSelection {
  direction: 'requirement_to_code'
  scenario_id: string
  changed_use_case_ids: string[]
  candidates: ClassCandidate[]
  unresolved: { use_case_id: string; reason: string }[]
  unparsed_candidate_ids: string[]
}

export interface BackwardSelection {
  direction: 'code_to_requirement'
  scenario_id: string
  changed_class_ids: string[]
  candidates: { use_case_id: string; triggering_class_ids: string[] }[]
  unassignable_class_ids: string[]
}

export type Selection = ForwardSelection | BackwardSelection

// --- Modellanalyse --------------------------------------------------------

export type AnswerState = 'answered' | 'invalid_format' | 'no_answer'

export type EntryStatus = 'change_proposed' | 'no_change_visible' | 'not_assessable'

export interface Entry {
  target_kind: 'method' | 'new_method' | 'class'
  target: string
  status: EntryStatus
  use_case_passage: string
  reason: string
  proposal: string | null
}

export interface CheckedEntry {
  entry: Entry
  method_ref: MethodRef | null
  problems: string[]
}

export interface CheckedAnswer {
  state: AnswerState
  problems: string[]
  entries: CheckedEntry[]
  unanswered_methods: MethodRef[]
  assumptions: string[]
  missing_context: string[]
}

export interface ClassAnalysis {
  class_id: string
  provider_name: string
  prompt_version: string
  prompt: string
  raw_response: string | null
  answer: CheckedAnswer
  requested_at: string
  finished_at: string
}

export interface ClassResult {
  class_id: string
  not_processed_reason: string | null
  analysis: ClassAnalysis | null
}

export interface ForwardRun {
  run_id: string
  scenario_id: string
  baseline_id: string
  started_at: string
  finished_at: string
  provider_name: string
  provider_settings: Record<string, string | number>
  prompt_version: string
  results: ClassResult[]
  unresolved: { use_case_id: string; reason: string }[]
}

export type DeviationStatus =
  | 'possible_deviation'
  | 'no_deviation_visible'
  | 'insufficient_information'

export interface Assessment {
  status: DeviationStatus
  affected_passage: string
  reason: string
  proposed_text: string | null
}

export interface CheckedAssessment {
  state: AnswerState
  problems: string[]
  assessment: Assessment | null
  assessment_problems: string[]
  assumptions: string[]
  missing_context: string[]
}

export interface UseCaseAnalysis {
  use_case_id: string
  provider_name: string
  prompt_version: string
  prompt: string
  raw_response: string | null
  answer: CheckedAssessment
  requested_at: string
  finished_at: string
}

export interface BackwardRun {
  run_id: string
  scenario_id: string
  baseline_id: string
  started_at: string
  finished_at: string
  provider_name: string
  provider_settings: Record<string, string | number>
  prompt_version: string
  results: UseCaseAnalysis[]
  unassignable_class_ids: string[]
}

export type Run = ForwardRun | BackwardRun

// Ein Lauf der Gegenrichtung erkennt sich an dieser Liste.
export function isBackwardRun(run: Run): run is BackwardRun {
  return 'unassignable_class_ids' in run
}

// --- Entscheidungen, Abdeckung, Abschluss ---------------------------------

export type DecisionKind = 'accepted' | 'rejected' | 'deferred'

export interface Decision {
  decision_id: string
  scenario_id: string
  run_id: string
  subject_id: string
  entry_index: number
  kind: DecisionKind
  revised_proposal: string | null
  decided_at: string
}

export interface Decisions {
  history: Decision[]
  current: Decision[]
}

export interface OpenItem {
  kind: string
  ref: string
  detail: string
}

export interface Coverage {
  run_id: string
  counts: Record<string, number>
  open_items: OpenItem[]
}

export interface Closure {
  run_id: string
  closed_at: string
  open_items_acknowledged: boolean
  note: string | null
  open_items: OpenItem[]
}

export interface CoverageResponse {
  coverage: Coverage
  closure: Closure | null
}

export type UiEventType = 'marking_shown' | 'comparison_shown' | 'context_shown'
