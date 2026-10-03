// Computes what the mapping view shows: which use cases, classes and links are
// visible and how each of them is highlighted. Graph and matrix both use the
// result, so they always show the same data and the same selection.
//
// Every artifact is addressed by a key: "uc:UC1" or "class:Buch.java".

import type { JavaClass, Project, ScenarioDetail, TraceLink, UseCase } from '../types';

export function useCaseKey(useCaseId: string) {
  return `uc:${useCaseId}`;
}

export function classKey(classId: string) {
  return `class:${classId}`;
}

export function parseKey(key: string): { kind: 'useCase' | 'class'; id: string } {
  if (key.startsWith('uc:')) return { kind: 'useCase', id: key.slice('uc:'.length) };
  return { kind: 'class', id: key.slice('class:'.length) };
}

// selected: chosen by the user
// linked:   directly connected to a selected artifact by a trace link
// indirect: connected to a linked artifact (second step), only if enabled
// dimmed:   something is selected, but this artifact is not related to it
// normal:   nothing is selected
export type HighlightState = 'selected' | 'linked' | 'indirect' | 'dimmed' | 'normal';

export interface ViewOptions {
  selection: Set<string>;
  subgraphOnly: boolean;
  showIndirect: boolean;
  showUnlinked: boolean;
}

// A scenario marked in graph and matrix: the changed artifact and its candidates.
export type ScenarioRole = 'changed' | 'candidate';

export interface ScenarioOverlay {
  title: string;
  changedKey: string;
  candidateKeys: string[];
}

export function buildScenarioOverlay(scenario: ScenarioDetail): ScenarioOverlay {
  const isCodeChange = scenario.changeType === 'code';
  return {
    title: scenario.title,
    changedKey: isCodeChange ? classKey(scenario.classId) : useCaseKey(scenario.useCaseId),
    candidateKeys: scenario.candidates.map((candidate) =>
      isCodeChange ? useCaseKey(candidate.artifactId) : classKey(candidate.artifactId),
    ),
  };
}

export interface MappingViewData {
  useCases: UseCase[];
  classes: JavaClass[];
  links: TraceLink[];
  isSubgraph: boolean;
  stateOf: (key: string) => HighlightState;
  linkStateOf: (link: TraceLink) => HighlightState;
  degreeOf: (key: string) => number;
  hasLink: (useCaseId: string, classId: string) => boolean;
  roleOf: (key: string) => ScenarioRole | null;
}

export function buildNeighbors(links: TraceLink[]): Map<string, Set<string>> {
  const neighbors = new Map<string, Set<string>>();
  const add = (from: string, to: string) => {
    if (!neighbors.has(from)) neighbors.set(from, new Set());
    neighbors.get(from)!.add(to);
  };
  for (const link of links) {
    add(useCaseKey(link.useCaseId), classKey(link.classId));
    add(classKey(link.classId), useCaseKey(link.useCaseId));
  }
  return neighbors;
}

function neighborsOf(keys: Set<string>, neighbors: Map<string, Set<string>>): Set<string> {
  const result = new Set<string>();
  for (const key of keys) {
    for (const neighbor of neighbors.get(key) ?? []) {
      if (!keys.has(neighbor)) result.add(neighbor);
    }
  }
  return result;
}

export function computeMappingView(
  project: Project,
  neighbors: Map<string, Set<string>>,
  options: ViewOptions,
  overlay: ScenarioOverlay | null,
): MappingViewData {
  const { selection } = options;
  const hasSelection = selection.size > 0;

  // Step 1: artifacts directly linked to the selection.
  const linked = neighborsOf(selection, neighbors);

  // Step 2: artifacts linked to those. For a selected use case these are the
  // other use cases sharing a class. A shared class does not mean the use
  // cases depend on each other, so they are shown as "indirect" only.
  const indirect = new Set<string>();
  if (options.showIndirect) {
    for (const key of neighborsOf(linked, neighbors)) {
      if (!selection.has(key)) indirect.add(key);
    }
  }

  const stateOf = (key: string): HighlightState => {
    if (!hasSelection) return 'normal';
    if (selection.has(key)) return 'selected';
    if (linked.has(key)) return 'linked';
    if (indirect.has(key)) return 'indirect';
    return 'dimmed';
  };

  const isSubgraph = options.subgraphOnly && hasSelection;
  const isVisible = (key: string) => {
    if (isSubgraph) return stateOf(key) !== 'dimmed';
    if (selection.has(key)) return true;
    return options.showUnlinked || neighbors.has(key);
  };

  const useCases = project.useCases.filter((uc) => isVisible(useCaseKey(uc.id)));
  const classes = project.classes.filter((cls) => isVisible(classKey(cls.id)));

  const visibleKeys = new Set([...useCases.map((uc) => useCaseKey(uc.id)), ...classes.map((cls) => classKey(cls.id))]);
  const links = project.links.filter(
    (link) => visibleKeys.has(useCaseKey(link.useCaseId)) && visibleKeys.has(classKey(link.classId)),
  );

  const linkStateOf = (link: TraceLink): HighlightState => {
    if (!hasSelection) return 'normal';
    const a = useCaseKey(link.useCaseId);
    const b = classKey(link.classId);
    if (selection.has(a) || selection.has(b)) return 'selected';
    const states = [stateOf(a), stateOf(b)];
    if (states.includes('dimmed')) return 'dimmed';
    return 'indirect';
  };

  const linkSet = new Set(project.links.map((link) => `${link.useCaseId}|${link.classId}`));

  return {
    useCases,
    classes,
    links,
    isSubgraph,
    stateOf,
    linkStateOf,
    degreeOf: (key) => neighbors.get(key)?.size ?? 0,
    hasLink: (useCaseId, classId) => linkSet.has(`${useCaseId}|${classId}`),
    roleOf: (key) => {
      if (key === overlay?.changedKey) return 'changed';
      if (overlay?.candidateKeys.includes(key)) return 'candidate';
      return null;
    },
  };
}

export function useCaseLabel(useCase: UseCase) {
  return useCase.title ? `${useCase.id}: ${useCase.title}` : useCase.id;
}
