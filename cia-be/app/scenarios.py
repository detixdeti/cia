"""Scenarios: a planned change, kept apart from the project files.

The candidates are taken from the declared trace links only:
- a use case changes: the classes linked to it
- code changes: the use cases linked to the changed class
"""

import json
from dataclasses import dataclass

from app.database import connect, now
from app.models import Analysis, Candidate, JavaClassDetail, Project, Proposal, ScenarioCreate, ScenarioDetail
from app.project_loader import natural_sort_key

# Proposals that need a decision before a scenario is completed.
# 'unclear' needs one too: the user marks it as checked.
CHANGE_PROPOSALS = ("modify", "remove", "add", "deviation")
NEEDS_DECISION = (*CHANGE_PROPOSALS, "unclear")


class ScenarioError(Exception):
    """The message is shown to the user."""


@dataclass
class NewScenario:
    title: str
    candidate_ids: list[str]
    use_case_id: str = ""
    original_text: str = ""
    new_text: str = ""
    class_id: str = ""
    method_signature: str = ""
    original_code: str = ""
    new_code: str = ""


def create_scenario(project: Project, request: ScenarioCreate, changed_class: JavaClassDetail | None) -> int:
    if request.change_type == "code":
        scenario = prepare_code_change(project, request, changed_class)
    else:
        scenario = prepare_use_case_change(project, request)
    if request.title.strip():
        scenario.title = request.title.strip()

    with connect() as connection:
        scenario_id = connection.execute(
            "INSERT INTO scenarios (project_id, title, change_type, use_case_id, original_text, new_text, "
            "class_id, method_signature, original_code, new_code, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                project.id,
                scenario.title,
                request.change_type,
                scenario.use_case_id,
                scenario.original_text,
                scenario.new_text,
                scenario.class_id,
                scenario.method_signature,
                scenario.original_code,
                scenario.new_code,
                now(),
            ),
        ).lastrowid
        connection.executemany(
            "INSERT INTO candidates (scenario_id, artifact_id) VALUES (?, ?)",
            [(scenario_id, artifact_id) for artifact_id in scenario.candidate_ids],
        )
    return scenario_id


def prepare_use_case_change(project: Project, request: ScenarioCreate) -> NewScenario:
    use_cases = {use_case.id: use_case for use_case in project.use_cases}
    use_case_id = request.use_case_id.strip()
    new_text = request.new_text.strip()

    if request.change_type == "add":
        if not use_case_id:
            raise ScenarioError("Bitte eine Kennung für den neuen Use Case angeben")
        if use_case_id in use_cases:
            raise ScenarioError(f"Use Case {use_case_id} existiert bereits")
        if not new_text:
            raise ScenarioError("Bitte den Text des neuen Use Cases angeben")
        if not request.class_ids:
            raise ScenarioError("Keine Zuordnung für die Analyse vorhanden: bitte mindestens eine Klasse auswählen")
        known_classes = {java_class.id for java_class in project.classes}
        unknown = [class_id for class_id in request.class_ids if class_id not in known_classes]
        if unknown:
            raise ScenarioError(f"Unbekannte Klassen: {', '.join(unknown)}")
        # A new use case has no trace links yet, the user chooses the classes.
        return NewScenario(
            title=f"{use_case_id} neu anlegen",
            candidate_ids=sorted(set(request.class_ids)),
            use_case_id=use_case_id,
            new_text=new_text,
        )

    if use_case_id not in use_cases:
        raise ScenarioError(f"Use Case {use_case_id} existiert nicht")
    original_text = use_cases[use_case_id].text
    linked_classes = sorted({link.class_id for link in project.links if link.use_case_id == use_case_id})

    if request.change_type == "deactivate":
        return NewScenario(
            title=f"{use_case_id} deaktivieren",
            candidate_ids=linked_classes,
            use_case_id=use_case_id,
            original_text=original_text,
        )

    if not new_text or new_text == original_text.strip():
        raise ScenarioError("Der neue Text unterscheidet sich nicht vom bisherigen Text")
    return NewScenario(
        title=f"{use_case_id} ändern",
        candidate_ids=linked_classes,
        use_case_id=use_case_id,
        original_text=original_text,
        new_text=new_text,
    )


def prepare_code_change(
    project: Project, request: ScenarioCreate, changed_class: JavaClassDetail | None
) -> NewScenario:
    if changed_class is None:
        raise ScenarioError(f"Klasse {request.class_id} existiert nicht")

    original_code = changed_class.source
    if request.method_signature:
        method = next((m for m in changed_class.methods if m.signature == request.method_signature), None)
        if method is None:
            raise ScenarioError(f"Methode {request.method_signature} existiert in {changed_class.id} nicht")
        lines = changed_class.source.split("\n")
        original_code = "\n".join(lines[method.start_line - 1 : method.end_line])

    if not request.new_code.strip() or request.new_code.strip() == original_code.strip():
        raise ScenarioError("Der geänderte Code unterscheidet sich nicht vom bisherigen Code")

    linked_use_cases = {link.use_case_id for link in project.links if link.class_id == changed_class.id}
    if not linked_use_cases:
        raise ScenarioError(f"{changed_class.id} ist keinem Use Case zugeordnet und daher nicht zuordenbar")

    changed_part = changed_class.id
    if request.method_signature:
        changed_part = f"{changed_class.id.removesuffix('.java')}.{request.method_signature}"
    return NewScenario(
        title=f"{changed_part} geändert",
        candidate_ids=sorted(linked_use_cases, key=natural_sort_key),
        class_id=changed_class.id,
        method_signature=request.method_signature,
        original_code=original_code,
        new_code=request.new_code,
    )


def list_scenarios(project_id: str) -> list[ScenarioDetail]:
    with connect() as connection:
        rows = connection.execute("SELECT id FROM scenarios WHERE project_id = ? ORDER BY id DESC", (project_id,))
        scenario_ids = [row["id"] for row in rows]
    return [get_scenario(scenario_id) for scenario_id in scenario_ids]


def get_scenario(scenario_id: int) -> ScenarioDetail | None:
    with connect() as connection:
        row = connection.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        if row is None:
            return None
        artifact_ids = [
            r["artifact_id"]
            for r in connection.execute("SELECT artifact_id FROM candidates WHERE scenario_id = ?", (scenario_id,))
        ]
        candidates = [
            Candidate(artifact_id=artifact_id, analysis=read_latest_analysis(connection, scenario_id, artifact_id))
            for artifact_id in sorted(artifact_ids, key=natural_sort_key)
        ]

    analyses = [candidate.analysis for candidate in candidates if candidate.analysis]
    analysed = sum(1 for analysis in analyses if analysis.status == "done")
    undecided = sum(
        1
        for analysis in analyses
        for proposal in analysis.proposals
        if proposal.assessment in NEEDS_DECISION and proposal.decision == "open"
    )
    open_count = len(candidates) - analysed + undecided

    if row["applied_at"]:
        # Applied is final: what was not accepted was simply not applied.
        status, open_count = "applied", 0
    elif not analyses:
        status = "created"
    elif any(analysis.status in ("pending", "running") for analysis in analyses):
        status = "running"
    elif open_count == 0:
        status = "completed"
    else:
        status = "review"

    return ScenarioDetail(
        **row,
        status=status,
        candidate_count=len(candidates),
        analysed_count=analysed,
        open_count=open_count,
        candidates=candidates,
    )


def read_latest_analysis(connection, scenario_id: int, artifact_id: str) -> Analysis | None:
    row = connection.execute(
        "SELECT * FROM analyses WHERE scenario_id = ? AND artifact_id = ? ORDER BY id DESC LIMIT 1",
        (scenario_id, artifact_id),
    ).fetchone()
    if row is None:
        return None

    proposals = [
        Proposal(**proposal)
        for proposal in connection.execute("SELECT * FROM proposals WHERE analysis_id = ? ORDER BY id", (row["id"],))
    ]
    return Analysis(**{**row, "call_sites": json.loads(row["call_sites"]), "proposals": proposals})


def queue_analyses(scenario_id: int, artifact_ids: list[str] | None = None) -> list[int]:
    """Creates pending analyses and returns their ids.

    Without artifact_ids, all candidates without a finished analysis are queued.
    A candidate that is already waiting or running is never queued twice.
    """
    scenario = get_scenario(scenario_id)
    if scenario.applied_at:
        raise ScenarioError("Das Szenario wurde bereits übernommen und kann nicht mehr analysiert werden")

    queued = []
    with connect() as connection:
        for candidate in scenario.candidates:
            status = candidate.analysis.status if candidate.analysis else None
            if artifact_ids is not None and candidate.artifact_id not in artifact_ids:
                continue
            if status in ("pending", "running") or (artifact_ids is None and status == "done"):
                continue
            cursor = connection.execute(
                "INSERT INTO analyses (scenario_id, artifact_id, status, created_at) VALUES (?, ?, 'pending', ?)",
                (scenario_id, candidate.artifact_id, now()),
            )
            queued.append(cursor.lastrowid)
    return queued


def set_decision(proposal_id: int, decision: str) -> bool:
    with connect() as connection:
        scenario = connection.execute(
            "SELECT s.applied_at FROM proposals p "
            "JOIN analyses a ON a.id = p.analysis_id JOIN scenarios s ON s.id = a.scenario_id "
            "WHERE p.id = ?",
            (proposal_id,),
        ).fetchone()
        if scenario is None:
            return False
        if scenario["applied_at"]:
            raise ScenarioError("Das Szenario wurde bereits übernommen, Entscheidungen sind nicht mehr änderbar")
        connection.execute(
            "UPDATE proposals SET decision = ?, decided_at = ? WHERE id = ?",
            (decision, None if decision == "open" else now(), proposal_id),
        )
    return True


def accept_all_changes(scenario_id: int) -> int:
    """Accepts every open change proposal of a scenario and returns how many were accepted.

    Proposals whose method or field does not exist are left open, they cannot be applied.
    """
    scenario = get_scenario(scenario_id)
    if scenario.applied_at:
        raise ScenarioError("Das Szenario wurde bereits übernommen, Entscheidungen sind nicht mehr änderbar")

    proposal_ids = [
        proposal.id
        for candidate in scenario.candidates
        if candidate.analysis
        for proposal in candidate.analysis.proposals
        if proposal.assessment in CHANGE_PROPOSALS and proposal.decision == "open" and not proposal.reference_problem
    ]
    with connect() as connection:
        connection.executemany(
            "UPDATE proposals SET decision = 'accepted', decided_at = ? WHERE id = ?",
            [(now(), proposal_id) for proposal_id in proposal_ids],
        )
    return len(proposal_ids)


def delete_scenario(scenario_id: int) -> bool:
    with connect() as connection:
        deleted = connection.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,)).rowcount
    return deleted > 0
