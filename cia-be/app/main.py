from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app import scenarios
from app.apply_scenario import apply_scenario, reset_applied_scenarios
from app.database import init_database
from app.impact_analysis import run_analyses
from app.models import (
    DecisionUpdate,
    JavaClassDetail,
    Project,
    ProjectSummary,
    ScenarioCreate,
    ScenarioDetail,
    ScenarioSummary,
)
from app.project_loader import delete_working_copy, find_project_dir, list_projects, load_class_detail, load_project
from app.scenarios import ScenarioError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    yield


app = FastAPI(title="CIA Backend", lifespan=lifespan)


@app.exception_handler(ScenarioError)
def scenario_error_handler(_request: Request, error: ScenarioError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


# --- Projects ---


@app.get("/api/projects", response_model=list[ProjectSummary])
def get_projects():
    return list_projects()


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    return load_project(project_dir_or_404(project_id))


@app.get("/api/projects/{project_id}/classes/{class_id}", response_model=JavaClassDetail)
def get_class(project_id: str, class_id: str):
    detail = load_class_detail(project_dir_or_404(project_id), class_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Klasse {class_id} nicht gefunden")
    return detail


@app.post("/api/projects/{project_id}/reset")
def reset_project(project_id: str):
    """Discards all applied scenarios, the project is read from the fixtures again."""
    project_dir_or_404(project_id)
    delete_working_copy(project_id)
    reset_applied_scenarios(project_id)
    return {"reset": project_id}


# --- Scenarios ---


@app.get("/api/projects/{project_id}/scenarios", response_model=list[ScenarioSummary])
def get_scenarios(project_id: str):
    project_dir_or_404(project_id)
    return scenarios.list_scenarios(project_id)


@app.post("/api/projects/{project_id}/scenarios", response_model=ScenarioDetail)
def create_scenario(project_id: str, request: ScenarioCreate):
    project_dir = project_dir_or_404(project_id)
    changed_class = load_class_detail(project_dir, request.class_id) if request.change_type == "code" else None
    scenario_id = scenarios.create_scenario(load_project(project_dir), request, changed_class)
    return scenarios.get_scenario(scenario_id)


@app.get("/api/scenarios/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: int):
    return scenario_or_404(scenario_id)


@app.delete("/api/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int):
    if not scenarios.delete_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Szenario nicht gefunden")
    return {"deleted": scenario_id}


@app.post("/api/scenarios/{scenario_id}/analyze", response_model=ScenarioDetail)
def analyze_scenario(scenario_id: int, background_tasks: BackgroundTasks):
    """Starts the analysis and returns at once. The frontend polls the scenario for progress."""
    scenario_or_404(scenario_id)
    background_tasks.add_task(run_analyses, scenarios.queue_analyses(scenario_id))
    return scenarios.get_scenario(scenario_id)


@app.post("/api/scenarios/{scenario_id}/candidates/{artifact_id}/analyze", response_model=ScenarioDetail)
def analyze_candidate(scenario_id: int, artifact_id: str, background_tasks: BackgroundTasks):
    scenario = scenario_or_404(scenario_id)
    if artifact_id not in [candidate.artifact_id for candidate in scenario.candidates]:
        raise HTTPException(status_code=404, detail=f"{artifact_id} ist kein Kandidat dieses Szenarios")
    background_tasks.add_task(run_analyses, scenarios.queue_analyses(scenario_id, [artifact_id]))
    return scenarios.get_scenario(scenario_id)


@app.post("/api/scenarios/{scenario_id}/apply", response_model=ScenarioDetail)
def apply(scenario_id: int):
    scenario_or_404(scenario_id)
    apply_scenario(scenario_id)
    return scenarios.get_scenario(scenario_id)


@app.post("/api/scenarios/{scenario_id}/accept-all")
def accept_all(scenario_id: int):
    scenario_or_404(scenario_id)
    return {"accepted": scenarios.accept_all_changes(scenario_id)}


@app.put("/api/proposals/{proposal_id}/decision")
def update_decision(proposal_id: int, update: DecisionUpdate):
    if not scenarios.set_decision(proposal_id, update.decision):
        raise HTTPException(status_code=404, detail="Vorschlag nicht gefunden")
    return {"id": proposal_id, "decision": update.decision}


def project_dir_or_404(project_id: str) -> Path:
    project_dir = find_project_dir(project_id)
    if project_dir is None:
        raise HTTPException(status_code=404, detail=f"Projekt {project_id} nicht gefunden")
    return project_dir


def scenario_or_404(scenario_id: int) -> ScenarioDetail:
    scenario = scenarios.get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Szenario nicht gefunden")
    return scenario
