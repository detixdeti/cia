// Alle deutschen Beschriftungen an einer Stelle.
// Keine Farbe steht allein fuer einen Zustand: Jeder hat eine Beschriftung
// (Konzept 4.8). Nichts wird als "in Ordnung" oder "gruen" dargestellt, wenn nur
// nichts gefunden wurde (Konzept 4.12).

import type {
  AnswerState,
  DecisionKind,
  Direction,
  DeviationStatus,
  EntryStatus,
  ScenarioState,
} from './types'

export const SCENARIO_STATE: Record<ScenarioState, string> = {
  created: 'angelegt',
  structurally_checked: 'strukturell geprüft',
  analysis_running: 'Analyse läuft',
  ready_for_review: 'zur Prüfung bereit',
  closed: 'abgeschlossen',
  discarded: 'verworfen',
}

export const ENTRY_STATUS: Record<EntryStatus, string> = {
  change_proposed: 'Änderung vorgeschlagen',
  no_change_visible: 'Im betrachteten Kontext kein Änderungsbedarf erkennbar',
  not_assessable: 'Nicht ausreichend beurteilbar',
}

export const DEVIATION_STATUS: Record<DeviationStatus, string> = {
  possible_deviation: 'Mögliche Verhaltensabweichung',
  no_deviation_visible: 'Im betrachteten Kontext keine Abweichung erkennbar',
  insufficient_information: 'Unzureichende Information',
}

export const ANSWER_STATE: Record<AnswerState, string> = {
  answered: 'beantwortet',
  invalid_format: 'Antwort nicht lesbar',
  no_answer: 'keine Antwort',
}

export const DECISION: Record<DecisionKind, string> = {
  accepted: 'angenommen',
  rejected: 'verworfen',
  deferred: 'zurückgestellt',
}

/** Was an einem Eintrag der Modellantwort nicht stimmt. */
export const PROBLEM: Record<string, string> = {
  unknown_method: 'Diese Methode gibt es in der Klasse nicht',
  already_exists: 'Als neu gemeldet, den Namen gibt es aber schon',
  duplicate: 'Dieselbe Stelle wird mehrfach genannt',
  incomplete: 'Unvollständig (Stelle, Begründung oder Vorschlag fehlt)',
  no_proposed_text: 'Kein Textvorschlag vorhanden',
}

/** Offene Fälle der Abdeckungsanzeige (Konzept 4.12). */
export const OPEN_KIND: Record<string, string> = {
  not_assigned: 'Nicht zugeordnet',
  not_processed: 'Nicht verarbeitet',
  not_assessable: 'Nicht ausreichend beurteilbar',
  unanswered_method: 'Das Modell sagt nichts dazu (offen, nicht „unverändert“)',
  entry_with_problem: 'Eintrag mit Problem',
  proposal_undecided: 'Vorschlag noch nicht entschieden',
  proposal_deferred: 'Vorschlag zurückgestellt',
}

export const COUNT: Record<string, string> = {
  imported_classes: 'Klassen importiert',
  imported_use_cases: 'Use Cases importiert',
  candidate_classes: 'Klassen strukturell zugeordnet (Kandidaten)',
  candidate_use_cases: 'Use Cases strukturell zugeordnet (Kandidaten)',
  prepared_classes: 'Klassen aufbereitet',
  analyzed_classes: 'Klassen vom Modell beantwortet',
  analyzed_use_cases: 'Use Cases vom Modell beantwortet',
  unassignable_classes: 'Geänderte Klassen ohne Zuordnung',
  unanswered_methods: 'Methoden ohne Aussage des Modells',
  not_assessable: 'Nicht ausreichend beurteilbar',
  insufficient_information: 'Unzureichende Information',
  no_change_visible: 'Im Kontext kein Änderungsbedarf erkennbar (keine Garantie)',
  no_deviation_visible: 'Im Kontext keine Abweichung erkennbar (keine Garantie)',
  proposals: 'Vorschläge insgesamt',
  proposals_accepted: 'angenommen',
  proposals_rejected: 'verworfen',
  proposals_deferred: 'zurückgestellt',
  proposals_undecided: 'noch nicht entschieden',
}

export const IMPORT_COUNT: Record<string, string> = {
  use_cases: 'Use Cases',
  classes: 'Java-Klassen',
  parsed_classes: 'davon verarbeitet',
  methods: 'Methoden erkannt',
  trace_links: 'Trace-Links (eindeutig)',
  read_link_lines: 'Zeilen der Link-Datei gelesen',
  duplicate_link_lines: 'davon doppelt deklariert',
  unlinked_classes: 'Klassen ohne Zuordnung',
  unlinked_use_cases: 'Use Cases ohne Zuordnung',
}

export const SEVERITY: Record<string, string> = {
  error: 'Fehler',
  warning: 'Warnung',
  info: 'Hinweis',
}

export const DIRECTION: Record<Direction, string> = {
  requirement_to_code: 'Anforderung ändern (Auswirkung auf den Code)',
  code_to_requirement: 'Code ändern (Auswirkung auf Use Cases)',
}

export const CHANGE_KIND: Record<string, string> = {
  deactivate: 'Deaktivieren',
  modify: 'Ändern',
  add: 'Neu anlegen',
}
