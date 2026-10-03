import type {
  Decision,
  JavaClassDetail,
  Project,
  ProjectSummary,
  ScenarioCreate,
  ScenarioDetail,
  ScenarioSummary,
} from './types';

async function request<T>(url: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    // FastAPI puts the error message into "detail"
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === 'string' ? error.detail : `${url} lieferte ${response.status}`);
  }
  return response.json();
}

const projectUrl = (projectId: string) => `/api/projects/${encodeURIComponent(projectId)}`;

export function fetchProjects(): Promise<ProjectSummary[]> {
  return request('/api/projects');
}

export function fetchProject(projectId: string): Promise<Project> {
  return request(projectUrl(projectId));
}

export function fetchClass(projectId: string, classId: string): Promise<JavaClassDetail> {
  return request(`${projectUrl(projectId)}/classes/${encodeURIComponent(classId)}`);
}

export function fetchScenarios(projectId: string): Promise<ScenarioSummary[]> {
  return request(`${projectUrl(projectId)}/scenarios`);
}

export function createScenario(projectId: string, scenario: ScenarioCreate): Promise<ScenarioDetail> {
  return request(`${projectUrl(projectId)}/scenarios`, 'POST', scenario);
}

export function fetchScenario(scenarioId: number): Promise<ScenarioDetail> {
  return request(`/api/scenarios/${scenarioId}`);
}

export function deleteScenario(scenarioId: number): Promise<unknown> {
  return request(`/api/scenarios/${scenarioId}`, 'DELETE');
}

// Starts the analysis in the background and returns at once.
export function startAnalysis(scenarioId: number): Promise<ScenarioDetail> {
  return request(`/api/scenarios/${scenarioId}/analyze`, 'POST');
}

export function startCandidateAnalysis(scenarioId: number, artifactId: string): Promise<ScenarioDetail> {
  return request(`/api/scenarios/${scenarioId}/candidates/${encodeURIComponent(artifactId)}/analyze`, 'POST');
}

export function setDecision(proposalId: number, decision: Decision): Promise<unknown> {
  return request(`/api/proposals/${proposalId}/decision`, 'PUT', { decision });
}

// Writes the scenario and its accepted proposals into the working copy of the project.
export function applyScenario(scenarioId: number): Promise<ScenarioDetail> {
  return request(`/api/scenarios/${scenarioId}/apply`, 'POST');
}

// Discards the working copy, the project is read from the original files again.
export function resetProject(projectId: string): Promise<unknown> {
  return request(`${projectUrl(projectId)}/reset`, 'POST');
}

// Accepts all open change proposals of the scenario and returns how many were accepted.
export function acceptAllChanges(scenarioId: number): Promise<{ accepted: number }> {
  return request(`/api/scenarios/${scenarioId}/accept-all`, 'POST');
}
