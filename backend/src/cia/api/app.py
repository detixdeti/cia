"""FastAPI-Anwendung des Prototyps.

Die Schnittstelle stellt Import (F1), Auswahl als Teilgraph (F2), die
Szenarioanlage (F3) und die strukturelle Kandidatenauswahl in beiden Richtungen
(Anteile von F4 und F6) bereit. Sie haengt von ``analysis/`` ab, nicht von einer
Modellanbindung. Die LLM-Bewertung (Konzept 4.5) kommt spaeter als eigener,
nachgelagerter Schritt und ersetzt die hier ausgewiesene Herkunft der
Kandidaten nicht.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from ..analysis.structural import (
    BackwardSelection,
    ForwardSelection,
    select_backward,
    select_forward,
    select_neighbourhood,
)
from ..domain.artifacts import JavaMethod, MethodSignature
from ..domain.baseline import Baseline
from ..domain.decision import Decision, current_decisions
from ..domain.ids import ClassId, UseCaseId
from ..domain.scenario import (
    CodeChange,
    Direction,
    IllegalTransition,
    RequirementChange,
    Scenario,
    ScenarioState,
)
from ..importing.project import ImportReport, import_from_texts, import_project
from ..llm.backward import run_backward_analysis
from ..llm.mock import ANTWORT_OHNE_BEWERTUNG, MockProvider
from ..llm.provider import LlmProvider
from ..llm.run import AnyRun, run_forward_analysis
from ..review.coverage import (
    Closure,
    Coverage,
    compute_backward_coverage,
    compute_coverage,
)
from .decision_input import DecisionInputError, build_decision, find_suggestion
from .graph import build_graph, build_subgraph
from .registry import Registry
from .scenario_input import ScenarioInputError, build_scenario
from .schemas import (
    BackwardSelectionOut,
    BaselineDetailOut,
    BaselineSummaryOut,
    ClassCandidateOut,
    ClassOut,
    CloseIn,
    CodeChangeOut,
    DecisionIn,
    DiagnosticOut,
    ForwardSelectionOut,
    GraphOut,
    ImportRequest,
    MethodOut,
    MethodRefOut,
    RequirementChangeModel,
    ScenarioCreate,
    ScenarioOut,
    SelectionOut,
    SignatureModel,
    SourceRangeOut,
    UiEventIn,
    UnresolvedChangeOut,
    UploadedFile,
    UploadRequest,
    UseCaseCandidateOut,
    UseCaseOut,
)

#: Herkunft der Oberflaeche im Entwicklungsbetrieb (Vite).
DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def create_app(
    registry: Registry | None = None,
    autoload: Path | list[Path] | None = None,
    provider: LlmProvider | None = None,
    protocol_dir: Path | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Baut die Anwendung.

    ``autoload`` importiert beim Start einen oder mehrere Projektstaende, damit die Oberflaeche
    ohne Eingabe eines Pfades etwas zeigen kann. ``provider`` ist das
    Sprachmodell; ohne Angabe antwortet der Mock, der nichts bewertet.
    ``protocol_dir`` ist das Verzeichnis, in das das Protokoll geschrieben wird;
    ohne Angabe bleibt es im Arbeitsspeicher. ``cors_origins`` nennt die
    Adressen, von denen die Oberflaeche das Backend aufrufen darf (Vorgabe: der
    Vite-Entwicklungsserver auf Port 5173).
    """
    app = FastAPI(title="CIA-Prototyp", version="0.1.0")
    app.state.registry = registry or Registry(protocol_dir)
    app.state.provider = provider or MockProvider(ANTWORT_OHNE_BEWERTUNG)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or DEV_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(router)

    if autoload is not None:
        paths = [autoload] if isinstance(autoload, Path) else autoload
        for p in paths:
            if p.is_dir():
                app.state.registry.add_report(import_project(p))
    return app


def get_registry(request: Request) -> Registry:
    return request.app.state.registry


def get_provider(request: Request) -> LlmProvider:
    return request.app.state.provider


RegistryDep = Annotated[Registry, Depends(get_registry)]
ProviderDep = Annotated[LlmProvider, Depends(get_provider)]
router = APIRouter(prefix="/api")


# --- Hilfen -----------------------------------------------------------------


def _report(registry: Registry, baseline_id: str) -> ImportReport:
    report = registry.report(baseline_id)
    if report is None:
        raise HTTPException(404, f"Ausgangsstand {baseline_id} ist nicht vorhanden")
    return report


def _scenario(registry: Registry, scenario_id: str) -> Scenario:
    scenario = registry.scenario(scenario_id)
    if scenario is None:
        raise HTTPException(404, f"Szenario {scenario_id} ist nicht vorhanden")
    return scenario


def _baseline_of(registry: Registry, scenario: Scenario) -> Baseline:
    return _report(registry, scenario.baseline_id).baseline


def _change_state(registry: Registry, scenario: Scenario, new_state: ScenarioState) -> None:
    """Wechselt den Zustand des Szenarios und haelt den Wechsel im Protokoll fest.

    Alle Zustandswechsel laufen hierueber, damit keiner unprotokolliert bleibt.
    Ein unzulaessiger Wechsel loest ``IllegalTransition`` aus, bevor etwas
    protokolliert wird.
    """
    old_state = scenario.state
    scenario.transition_to(new_state)
    registry.protocol.record(
        scenario.id, "state_changed", {"from": old_state, "to": new_state}
    )


def _signature_out(signature: MethodSignature) -> SignatureModel:
    return SignatureModel(name=signature.name, parameter_types=list(signature.parameter_types))


def _method_out(method: JavaMethod) -> MethodOut:
    ref = method.ref
    return MethodOut(
        ref=MethodRefOut(
            baseline_id=ref.baseline_id,
            class_id=ref.class_id,
            signature=_signature_out(ref.signature),
            source_range=SourceRangeOut(
                start_line=ref.source_range.start_line,
                end_line=ref.source_range.end_line,
                start_byte=ref.source_range.start_byte,
                end_byte=ref.source_range.end_byte,
            ),
        ),
        is_constructor=method.is_constructor,
        source=method.source,
    )


def _requirement_change_out(change: RequirementChange) -> RequirementChangeModel:
    return RequirementChangeModel(
        kind=change.kind,
        use_case_id=change.use_case_id,
        target_text=change.target_text,
        manual_class_ids=list(change.manual_class_ids),
    )


def _code_change_out(change: CodeChange) -> CodeChangeOut:
    return CodeChangeOut(
        class_id=change.class_id,
        before=change.before,
        after=change.after,
        signature=_signature_out(change.signature) if change.signature else None,
    )


def _scenario_out(scenario: Scenario) -> ScenarioOut:
    return ScenarioOut(
        scenario_id=scenario.id,
        baseline_id=scenario.baseline_id,
        title=scenario.title,
        direction=scenario.direction,
        state=scenario.state,
        created_at=scenario.created_at,
        requirement_changes=[_requirement_change_out(c) for c in scenario.requirement_changes],
        code_changes=[_code_change_out(c) for c in scenario.code_changes],
    )


def _forward_out(scenario_id: str, selection: ForwardSelection) -> ForwardSelectionOut:
    return ForwardSelectionOut(
        scenario_id=scenario_id,
        changed_use_case_ids=sorted(selection.changed_use_case_ids),
        candidates=[
            ClassCandidateOut(
                class_id=c.class_id,
                triggering_use_case_ids=sorted(c.triggering_use_case_ids),
                preservation_context_ids=sorted(c.preservation_context_ids),
                parsed=c.parsed,
            )
            for c in selection.candidates
        ],
        unresolved=[
            UnresolvedChangeOut(use_case_id=u.use_case_id, reason=u.reason)
            for u in selection.unresolved
        ],
        unparsed_candidate_ids=sorted(selection.unparsed_candidate_ids),
    )


def _backward_out(scenario_id: str, selection: BackwardSelection) -> BackwardSelectionOut:
    return BackwardSelectionOut(
        scenario_id=scenario_id,
        changed_class_ids=sorted(selection.changed_class_ids),
        candidates=[
            UseCaseCandidateOut(
                use_case_id=c.use_case_id,
                triggering_class_ids=sorted(c.triggering_class_ids),
            )
            for c in selection.candidates
        ],
        unassignable_class_ids=sorted(selection.unassignable_class_ids),
    )


def _select(baseline: Baseline, scenario: Scenario) -> ForwardSelectionOut | BackwardSelectionOut:
    if scenario.direction is Direction.REQUIREMENT_TO_CODE:
        return _forward_out(scenario.id, select_forward(baseline, scenario))
    return _backward_out(scenario.id, select_backward(baseline, scenario))


# --- Import und Baseline (F1) ------------------------------------------------


@router.post("/baselines", response_model=BaselineDetailOut, status_code=201)
def import_baseline(body: ImportRequest, registry: RegistryDep) -> BaselineDetailOut:
    root = Path(body.path).expanduser()
    if not root.is_dir():
        raise HTTPException(422, f"{body.path} ist kein Verzeichnis")
    report = import_project(root, label=body.label)
    registry.add_report(report)
    return _detail(report)


#: Obergrenzen fuer einen Upload. Sie schuetzen den Prototyp vor versehentlich
#: riesigen Ordnern, sind aber keine fachliche Grenze.
MAX_UPLOAD_FILES = 2000
MAX_UPLOAD_CHARS = 10_000_000


def _accepted(files: list[UploadedFile], endings: tuple[str, ...]) -> tuple[list[tuple[str, str]], list[str]]:
    """Trennt Dateien nach Endung in verwendete (Pfad, Inhalt) und ignorierte Pfade."""
    used: list[tuple[str, str]] = []
    ignored: list[str] = []
    for file in files:
        path = file.path.replace("\\", "/").strip().lstrip("/")
        if not path:
            raise HTTPException(422, "Eine hochgeladene Datei hat keinen Namen")
        if path.lower().endswith(endings):
            used.append((path, file.content))
        else:
            ignored.append(path)
    return sorted(used), ignored


@router.post("/baselines/upload", response_model=BaselineDetailOut, status_code=201)
def upload_baseline(body: UploadRequest, registry: RegistryDep) -> BaselineDetailOut:
    """Importiert einen Projektstand aus hochgeladenen Dateiinhalten.

    Es wird nichts auf die Platte geschrieben. Ein Upload ergibt immer einen
    neuen Ausgangsstand, ein bestehender wird nie ueberschrieben (Konzept 4.2).
    Fehler in den Dateien stehen als Befunde im Ergebnis; nur ein leerer Upload
    oder ein zu grosser wird abgewiesen.
    """
    files = [*body.use_cases, *body.sources]
    if body.trace_links is not None:
        files.append(body.trace_links)
    if not files:
        raise HTTPException(422, "Es wurde nichts hochgeladen")
    if len(files) > MAX_UPLOAD_FILES or sum(len(f.content) for f in files) > MAX_UPLOAD_CHARS:
        raise HTTPException(413, "Der Upload ist zu gross fuer den Prototyp")

    use_cases, ignored_use_cases = _accepted(body.use_cases, (".md", ".txt"))
    sources, ignored_sources = _accepted(body.sources, (".java",))
    link_name = "tracelinks.txt"
    if body.trace_links is not None:
        link_name = body.trace_links.path.replace("\\", "/").rsplit("/", 1)[-1] or link_name

    report = import_from_texts(
        label=body.label or "Upload",
        # Bei Use Cases zaehlt nur der Dateiname, nicht der Ordner.
        use_cases=[(path.rsplit("/", 1)[-1], content) for path, content in use_cases],
        sources=sources,
        trace_links=body.trace_links.content if body.trace_links is not None else None,
        trace_link_name=link_name,
        ignored_files=(*ignored_use_cases, *ignored_sources),
    )
    registry.add_report(report)
    return _detail(report)


@router.get("/info")
def get_info(provider: ProviderDep) -> dict:
    """Welcher Modellanbieter laeuft. Die Oberflaeche zeigt es dauerhaft an,
    damit Beispielantworten nicht mit echten Bewertungen verwechselt werden."""
    return {"provider": provider.name, "settings": provider.settings}


@router.get("/baselines", response_model=list[BaselineSummaryOut])
def list_baselines(registry: RegistryDep) -> list[dict]:
    return [report.summary() for report in registry.reports()]


@router.get("/baselines/{baseline_id}", response_model=BaselineDetailOut)
def get_baseline(baseline_id: str, registry: RegistryDep) -> BaselineDetailOut:
    return _detail(_report(registry, baseline_id))


def _detail(report: ImportReport) -> BaselineDetailOut:
    return BaselineDetailOut(
        **report.summary(),
        diagnostic_entries=[
            DiagnosticOut(
                code=d.code.value,
                severity=d.severity.value,
                message=d.message,
                source_file=d.source_file,
                line_number=d.line_number,
            )
            for d in report.diagnostics
        ],
    )


# --- Graph und Auswahl (F2) --------------------------------------------------


@router.get("/baselines/{baseline_id}/graph", response_model=GraphOut)
def get_graph(baseline_id: str, registry: RegistryDep) -> GraphOut:
    return build_graph(_report(registry, baseline_id).baseline)


@router.get("/baselines/{baseline_id}/subgraph", response_model=GraphOut)
def get_subgraph(
    baseline_id: str,
    registry: RegistryDep,
    use_case: Annotated[list[str] | None, Query()] = None,
    class_ids: Annotated[list[str] | None, Query(alias="class")] = None,
) -> GraphOut:
    baseline = _report(registry, baseline_id).baseline
    selected_use_case_ids = use_case or []
    selected_class_ids = class_ids or []
    if not selected_use_case_ids and not selected_class_ids:
        raise HTTPException(422, "Es ist weder ein Use Case noch eine Klasse ausgewaehlt")

    unknown = [u for u in selected_use_case_ids if UseCaseId(u) not in baseline.use_cases]
    unknown += [c for c in selected_class_ids if ClassId(c) not in baseline.classes]
    if unknown:
        raise HTTPException(404, "Unbekannte Artefakte: " + ", ".join(unknown))

    hood = select_neighbourhood(
        baseline.trace_graph,
        [UseCaseId(u) for u in selected_use_case_ids],
        [ClassId(c) for c in selected_class_ids],
    )
    return build_subgraph(baseline, hood)


# --- Artefaktdetails -----------------------------------------------------------


@router.get("/baselines/{baseline_id}/use-cases/{use_case_id}", response_model=UseCaseOut)
def get_use_case(baseline_id: str, use_case_id: str, registry: RegistryDep) -> UseCaseOut:
    baseline = _report(registry, baseline_id).baseline
    use_case = baseline.use_case(UseCaseId(use_case_id))
    if use_case is None:
        raise HTTPException(404, f"Use Case {use_case_id} ist nicht vorhanden")
    class_ids = baseline.trace_graph.classes_of(use_case.id)
    return UseCaseOut(
        id=use_case.id,
        title=use_case.title,
        text=use_case.text,
        source_file=use_case.source_file,
        active=use_case.active,
        class_ids=sorted(class_ids),
        linked=bool(class_ids),
    )


@router.get("/baselines/{baseline_id}/classes/{class_id}", response_model=ClassOut)
def get_class(baseline_id: str, class_id: str, registry: RegistryDep) -> ClassOut:
    baseline = _report(registry, baseline_id).baseline
    java_class = baseline.java_class(ClassId(class_id))
    if java_class is None:
        raise HTTPException(404, f"Klasse {class_id} ist nicht vorhanden")
    use_case_ids = baseline.trace_graph.use_cases_of(java_class.id)
    return ClassOut(
        id=java_class.id,
        file_name=java_class.file_name,
        relative_path=java_class.relative_path,
        source=java_class.source,
        parsed=java_class.parsed,
        parse_error=java_class.parse_error,
        methods=[_method_out(m) for m in java_class.methods],
        use_case_ids=sorted(use_case_ids),
        linked=bool(use_case_ids),
    )


# --- Szenarien (F3) und strukturelle Auswahl -------------------------------------


@router.post(
    "/baselines/{baseline_id}/scenarios", response_model=ScenarioOut, status_code=201
)
def create_scenario(
    baseline_id: str, body: ScenarioCreate, registry: RegistryDep
) -> ScenarioOut:
    report = _report(registry, baseline_id)
    baseline = report.baseline
    try:
        scenario = build_scenario(baseline, body)
    except ScenarioInputError as error:
        raise HTTPException(422, error.problems) from error

    # Die Auswahl ist rein strukturell und reproduzierbar. Erst nach ihrer
    # Berechnung gilt das Szenario als strukturell geprueft (Konzept 4.8).
    _select(baseline, scenario)
    registry.add_scenario(scenario)
    registry.protocol.record(
        scenario.id,
        "scenario_created",
        {"baseline": report.summary(), "scenario": _scenario_out(scenario)},
    )
    _change_state(registry, scenario, ScenarioState.STRUCTURALLY_CHECKED)
    return _scenario_out(scenario)


@router.get("/baselines/{baseline_id}/scenarios", response_model=list[ScenarioOut])
def list_scenarios(baseline_id: str, registry: RegistryDep) -> list[ScenarioOut]:
    """Alle Szenarien eines Ausgangsstands, das aelteste zuerst."""
    _report(registry, baseline_id)
    return [_scenario_out(s) for s in registry.scenarios_of(baseline_id)]


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: str, registry: RegistryDep) -> ScenarioOut:
    return _scenario_out(_scenario(registry, scenario_id))


@router.get("/scenarios/{scenario_id}/selection", response_model=SelectionOut)
def get_selection(scenario_id: str, registry: RegistryDep):
    scenario = _scenario(registry, scenario_id)
    return _select(_baseline_of(registry, scenario), scenario)


@router.post("/scenarios/{scenario_id}/discard", response_model=ScenarioOut)
def discard_scenario(scenario_id: str, registry: RegistryDep) -> ScenarioOut:
    """Verwirft ein Szenario, ohne einen Soll-Zustand zu erzeugen (Konzept 4.12).

    Der Ausgangsstand bleibt unveraendert; bisherige Ergebnisse bleiben abrufbar.
    """
    scenario = _scenario(registry, scenario_id)
    try:
        _change_state(registry, scenario, ScenarioState.DISCARDED)
    except IllegalTransition as error:
        raise HTTPException(409, str(error)) from error
    return _scenario_out(scenario)


# --- Analyse durch das Modell (F4) ---------------------------------------------------


@router.post("/scenarios/{scenario_id}/analyses", response_model=AnyRun, status_code=201)
def start_analysis(scenario_id: str, registry: RegistryDep, provider: ProviderDep) -> AnyRun:
    """Fragt das Modell zu allen Kandidaten des Szenarios.

    In der Anforderungsrichtung sind das die Kandidatenklassen, in der
    Gegenrichtung die Kandidaten-Use-Cases.

    Der Aufruf wartet, bis der Lauf fertig ist. Ein neuer Aufruf erzeugt einen
    neuen Lauf mit eigener Kennung; fruehere Laeufe bleiben abrufbar.
    """
    scenario = _scenario(registry, scenario_id)
    baseline = _baseline_of(registry, scenario)

    try:
        _change_state(registry, scenario, ScenarioState.ANALYSIS_RUNNING)
    except IllegalTransition as error:
        raise HTTPException(409, str(error)) from error

    try:
        if scenario.direction is Direction.REQUIREMENT_TO_CODE:
            run = run_forward_analysis(baseline, scenario, provider)
        else:
            run = run_backward_analysis(baseline, scenario, provider)
    except Exception as error:
        # Bei einem unerwarteten Fehler zurueck in den vorherigen Zustand, damit
        # das Szenario nicht dauerhaft als "Analyse laeuft" haengen bleibt.
        registry.protocol.record(scenario.id, "analysis_aborted", {"error": repr(error)})
        _change_state(registry, scenario, ScenarioState.STRUCTURALLY_CHECKED)
        raise

    registry.add_run(run)
    registry.protocol.record_run(run)
    # "Zur Pruefung bereit" heisst nicht, dass alles geklaert ist. Offene Faelle
    # stehen im Lauf selbst (Konzept 4.8).
    _change_state(registry, scenario, ScenarioState.READY_FOR_REVIEW)
    return run


@router.get("/scenarios/{scenario_id}/analyses", response_model=list[AnyRun])
def list_analyses(scenario_id: str, registry: RegistryDep) -> list[AnyRun]:
    _scenario(registry, scenario_id)
    return registry.runs(scenario_id)


# --- Entscheidungen des Anwenders (F5) --------------------------------------------------


@router.post("/scenarios/{scenario_id}/decisions", response_model=Decision, status_code=201)
def create_decision(scenario_id: str, body: DecisionIn, registry: RegistryDep) -> Decision:
    """Haelt fest, ob der Anwender einen Vorschlag annimmt, verwirft oder zurueckstellt.

    Die Entscheidung wird angehaengt. Eine fruehere zum selben Vorschlag bleibt
    erhalten; die letzte gilt (siehe ``current`` in der Liste).
    """
    scenario = _scenario(registry, scenario_id)
    if scenario.state is not ScenarioState.READY_FOR_REVIEW:
        raise HTTPException(
            409, f"Entscheidungen sind im Zustand {scenario.state.value} nicht moeglich"
        )

    runs = registry.runs(scenario_id)
    try:
        decision = build_decision(scenario, runs, body)
    except DecisionInputError as error:
        raise HTTPException(422, error.problems) from error

    registry.add_decision(decision)
    run = next(r for r in runs if r.run_id == decision.run_id)
    suggestion = find_suggestion(run, decision.subject_id, decision.entry_index)
    registry.protocol.record(
        scenario.id,
        "decision",
        {
            "decision": decision,
            "target": suggestion.target,
            "original_proposal": suggestion.proposal,
        },
    )
    return decision


@router.get("/scenarios/{scenario_id}/decisions")
def list_decisions(scenario_id: str, registry: RegistryDep) -> dict:
    """Alle Entscheidungen in der Reihenfolge ihrer Abgabe und die jeweils letzte je Vorschlag."""
    _scenario(registry, scenario_id)
    history = registry.decisions(scenario_id)
    return {"history": history, "current": current_decisions(history)}


# --- Protokoll (F7) --------------------------------------------------------------------


@router.get("/scenarios/{scenario_id}/protocol")
def get_protocol(scenario_id: str, registry: RegistryDep) -> list[dict]:
    _scenario(registry, scenario_id)
    return registry.protocol.records(scenario_id)


# --- Abdeckung und Abschluss (Konzept 4.8 und 4.12) ----------------------------------


def _coverage_of(registry: Registry, scenario: Scenario, run: AnyRun) -> Coverage:
    """Berechnet die Abdeckung passend zur Richtung des Laufs."""
    baseline = _baseline_of(registry, scenario)
    decisions = registry.decisions(scenario.id)
    if scenario.direction is Direction.REQUIREMENT_TO_CODE:
        return compute_coverage(baseline, run, decisions)
    return compute_backward_coverage(baseline, run, decisions)


@router.get("/scenarios/{scenario_id}/coverage")
def get_coverage(scenario_id: str, registry: RegistryDep) -> dict:
    """Zaehlwerte und offene Faelle des letzten Analyselaufs.

    Ist das Szenario abgeschlossen, steht auch der Abschluss mit den damals
    offenen Faellen darin.
    """
    scenario = _scenario(registry, scenario_id)
    run = registry.latest_run(scenario_id)
    if run is None:
        raise HTTPException(409, "Es liegt noch kein Analyselauf vor")
    coverage = _coverage_of(registry, scenario, run)
    return {"coverage": coverage, "closure": registry.closure(scenario_id)}


@router.post("/scenarios/{scenario_id}/close", response_model=Closure)
def close_scenario(scenario_id: str, body: CloseIn, registry: RegistryDep) -> Closure:
    """Schliesst ein Szenario ab.

    Bestehen noch offene Faelle, muss der Anwender das ausdruecklich bestaetigen
    und begruenden. Der Abschluss haelt sie fest; sie bleiben danach sichtbar.
    """
    scenario = _scenario(registry, scenario_id)
    run = registry.latest_run(scenario_id)
    if scenario.state is not ScenarioState.READY_FOR_REVIEW or run is None:
        raise HTTPException(
            409, f"Ein Szenario im Zustand {scenario.state.value} laesst sich nicht abschliessen"
        )

    coverage = _coverage_of(registry, scenario, run)
    note = body.note.strip() if body.note else None

    if coverage.open_items:
        if not body.acknowledge_open_items:
            raise HTTPException(
                409,
                {
                    "message": "Es gibt offene Faelle. Zum Abschluss muessen sie bestaetigt werden.",
                    "open_items": jsonable_encoder(coverage.open_items),
                },
            )
        if not note:
            raise HTTPException(422, "Ein Abschluss mit offenen Faellen braucht eine Begruendung (note)")

    closure = Closure(
        run_id=run.run_id,
        closed_at=datetime.now(timezone.utc),
        open_items_acknowledged=bool(coverage.open_items),
        note=note,
        open_items=coverage.open_items,
    )
    registry.add_closure(closure, scenario_id)
    registry.protocol.record(
        scenario.id, "scenario_closed", {"closure": closure, "counts": coverage.counts}
    )
    _change_state(registry, scenario, ScenarioState.CLOSED)
    return closure


# --- Anzeige-Ereignisse der Oberflaeche (F7) --------------------------------------------


@router.post("/scenarios/{scenario_id}/events", status_code=201)
def add_ui_event(scenario_id: str, body: UiEventIn, registry: RegistryDep) -> dict:
    """Haelt fest, was die Oberflaeche dem Anwender angezeigt hat.

    Konzept 4.13: Das Protokoll soll erkennen lassen, welche Informationen
    tatsaechlich angezeigt wurden, insbesondere Markierungen und Vergleiche. Das
    kann nur die Oberflaeche melden.
    """
    _scenario(registry, scenario_id)
    return registry.protocol.record(scenario_id, "ui_event", body)
