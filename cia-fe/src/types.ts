// Mirrors the JSON returned by the backend (see cia-be/app/models.py).

export interface ProjectSummary {
  id: string;
  name: string;
}

export interface UseCase {
  id: string;
  title: string;
  text: string;
}

export interface JavaClass {
  id: string;
  path: string;
}

export interface JavaMethod {
  name: string;
  signature: string; // e.g. "ausleihen(Mitglied, Buch)", unique within a class
  isConstructor: boolean;
  startLine: number; // 1-based, inclusive
  endLine: number;
}

export interface JavaField {
  name: string; // e.g. "LEIHFRIST_TAGE"
  declaration: string; // e.g. "private static final int LEIHFRIST_TAGE = 28;"
  startLine: number;
  endLine: number;
}

export interface JavaClassDetail {
  id: string;
  path: string;
  source: string;
  methods: JavaMethod[];
  fields: JavaField[];
}

export interface TraceLink {
  useCaseId: string;
  classId: string;
}

export interface Project {
  id: string;
  name: string;
  useCases: UseCase[];
  classes: JavaClass[];
  links: TraceLink[];
  warnings: string[];
  modified: boolean; // true if applied scenarios changed the working copy
}

// --- Scenarios and impact analysis ---

// 'deactivate' | 'modify' | 'add' change a use case (candidates are classes),
// 'code' changes a class or method (candidates are use cases).
export type ChangeType = 'deactivate' | 'modify' | 'add' | 'code';
export type Decision = 'open' | 'accepted' | 'rejected';
export type Assessment =
  // use case changed -> method of a linked class
  | 'modify'
  | 'remove'
  | 'add'
  | 'no_change'
  // code changed -> linked use case
  | 'deviation'
  | 'no_deviation'
  // both directions
  | 'unclear';
export type AnalysisStatus = 'pending' | 'running' | 'done' | 'failed';
export type ScenarioStatus = 'created' | 'running' | 'review' | 'completed' | 'applied';

export interface ScenarioCreate {
  changeType: ChangeType;
  useCaseId?: string;
  newText?: string;
  title?: string;
  classIds?: string[];
  classId?: string;
  methodSignature?: string;
  newCode?: string;
}

export interface Proposal {
  id: number;
  target: string; // method signature, or the use case id for a code change
  assessment: Assessment;
  reason: string;
  requirementReference: string;
  originalCode: string; // current method code, or current use case text
  proposedCode: string; // proposed method code, or proposed use case text
  referenceProblem: string; // '' if the reference was checked successfully
  decision: Decision;
  decidedAt: string | null;
}

export interface CallSite {
  classId: string;
  methodSignature: string; // '' outside of methods
  lineNumber: number;
  line: string;
}

export interface Analysis {
  id: number;
  status: AnalysisStatus;
  statusMessage: string;
  error: string;
  classNote: string;
  callSites: CallSite[];
  model: string;
  promptVersion: string;
  prompt: string;
  rawAnswer: string;
  reasoning: string;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  proposals: Proposal[];
}

export interface Candidate {
  artifactId: string; // class id, or use case id for a code change
  analysis: Analysis | null;
}

export interface ScenarioSummary {
  id: number;
  projectId: string;
  title: string;
  changeType: ChangeType;
  useCaseId: string;
  classId: string;
  methodSignature: string;
  createdAt: string;
  appliedAt: string | null; // when the scenario was applied to the working copy
  status: ScenarioStatus;
  candidateCount: number;
  analysedCount: number;
  openCount: number;
}

export interface ScenarioDetail extends ScenarioSummary {
  originalText: string;
  newText: string;
  originalCode: string;
  newCode: string;
  candidates: Candidate[];
}
