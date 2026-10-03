"""Runs the model for one candidate and checks its answer.

- A use case changed: which methods and fields of a linked class must change?
- Code changed: is a linked use case still fulfilled?

Every reference in the answer is checked against the parsed class. A failed
call or an unreadable answer marks the analysis as failed; it is never turned
into "no change needed".
"""

import json
import threading

from app.call_sites import find_call_sites
from app.database import connect, now
from app.llm_client import LLM_MODEL, LlmError, ask_llm
from app.models import JavaClassDetail, JavaField, JavaMethod, Project
from app.project_loader import find_project_dir, load_class_detail, load_project
from app.prompts import (
    CODE_CHANGE_SYSTEM_PROMPT,
    PROMPT_VERSION,
    REQUIREMENT_CHANGE_SYSTEM_PROMPT,
    build_code_change_prompt,
    build_requirement_change_prompt,
)

CODE_ASSESSMENTS = ("modify", "remove", "add", "no_change", "unclear")
USE_CASE_ASSESSMENTS = ("deviation", "no_deviation", "unclear")

# Free models are rate limited, so only one model call runs at a time.
# The other analyses stay "pending" until it is their turn.
model_lock = threading.Lock()


class AnalysisError(Exception):
    pass


def run_analyses(analysis_ids: list[int]) -> None:
    """Runs the analyses one after another. Called as a background task."""
    for analysis_id in analysis_ids:
        with model_lock:
            run_analysis(analysis_id)


def run_analysis(analysis_id: int) -> None:
    with connect() as connection:
        analysis = connection.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        if analysis is None or analysis["status"] != "pending":
            return  # the scenario was deleted in the meantime
        scenario = connection.execute("SELECT * FROM scenarios WHERE id = ?", (analysis["scenario_id"],)).fetchone()

    try:
        project_dir = find_project_dir(scenario["project_id"])
        project = load_project(project_dir)
        if scenario["change_type"] == "code":
            analyse_use_case(analysis_id, scenario, project, analysis["artifact_id"])
        else:
            analyse_class(analysis_id, scenario, project, project_dir, analysis["artifact_id"])
    except (LlmError, AnalysisError) as error:
        update_analysis(analysis_id, status="failed", status_message="", error=str(error), finished_at=now())
    except Exception as error:
        # Anything else must be visible too, otherwise the analysis would stay "running" forever.
        update_analysis(
            analysis_id, status="failed", status_message="", error=f"Interner Fehler: {error}", finished_at=now()
        )


def ask_model(analysis_id: int, system_prompt: str, prompt: str) -> str:
    update_analysis(
        analysis_id,
        status="running",
        status_message="Modell wird befragt …",
        started_at=now(),
        prompt=prompt,
        prompt_version=PROMPT_VERSION,
        model=LLM_MODEL,
    )
    answer = ask_llm(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        on_wait=lambda message: update_analysis(analysis_id, status_message=message),
    )
    update_analysis(analysis_id, raw_answer=answer.content, reasoning=answer.reasoning or "", model=answer.model)
    return answer.content


# --- A use case changed: check a linked class ---


def analyse_class(analysis_id: int, scenario, project: Project, project_dir, class_id: str) -> None:
    detail = load_class_detail(project_dir, class_id)
    if detail is None:
        raise AnalysisError(f"Klasse {class_id} wurde im Projekt nicht gefunden")

    call_sites = find_call_sites(project_dir, detail)
    update_analysis(analysis_id, call_sites=json.dumps([site.model_dump() for site in call_sites]))

    # The other use cases of this class stay valid and must keep working.
    texts = {use_case.id: use_case.text for use_case in project.use_cases}
    other_use_cases = [
        (link.use_case_id, texts[link.use_case_id])
        for link in project.links
        if link.class_id == class_id and link.use_case_id != scenario["use_case_id"]
    ]

    prompt = build_requirement_change_prompt(
        change_type=scenario["change_type"],
        use_case_id=scenario["use_case_id"],
        original_text=scenario["original_text"],
        new_text=scenario["new_text"],
        class_id=class_id,
        source_with_line_numbers=add_line_numbers(detail.source),
        method_signatures=[method.signature for method in detail.methods],
        field_declarations=[f"{field.name}: {field.declaration}" for field in detail.fields],
        other_use_cases=other_use_cases,
        call_sites=call_sites,
    )
    answer = ask_model(analysis_id, REQUIREMENT_CHANGE_SYSTEM_PROMPT, prompt)

    class_note, proposals = parse_code_proposals(answer, detail)
    save_proposals(analysis_id, proposals)
    update_analysis(analysis_id, status="done", status_message="", class_note=class_note, finished_at=now())


def add_line_numbers(source: str) -> str:
    return "\n".join(f"{number:4d}  {line}" for number, line in enumerate(source.split("\n"), start=1))


def parse_code_proposals(answer: str, detail: JavaClassDetail) -> tuple[str, list[dict]]:
    """Reads the proposals and checks that each method or field exists in the class."""
    data = extract_json(answer)
    if not isinstance(data.get("proposals"), list):
        raise AnalysisError("Antwort des Modells enthält keine Liste 'proposals'")

    source_lines = detail.source.split("\n")
    proposals = []
    for item in data["proposals"]:
        if not isinstance(item, dict):
            continue

        target = str(item.get("signature", "")).strip()
        assessment = str(item.get("assessment", "")).strip()
        problem = ""
        if assessment not in CODE_ASSESSMENTS:
            problem = f"Unbekannte Einschätzung '{assessment}', als nicht beurteilbar behandelt"
            assessment = "unclear"

        member = find_member(detail, target)
        original_code = ""
        if assessment == "add":
            if member is not None:
                problem = f"{target} existiert bereits, als neues Element vorgeschlagen"
        elif member is None:
            problem = f"Methode oder Feld {target} existiert in {detail.id} nicht"
        else:
            target = member.signature if isinstance(member, JavaMethod) else member.name
            original_code = "\n".join(source_lines[member.start_line - 1 : member.end_line])

        proposals.append(
            {
                "target": target,
                "assessment": assessment,
                "reason": str(item.get("reason", "")),
                "requirement_reference": str(item.get("requirement_reference", "")),
                "original_code": original_code,
                "proposed_code": str(item.get("proposed_code", "")) if assessment in ("modify", "add") else "",
                "reference_problem": problem,
            }
        )

    return str(data.get("class_note", "")), proposals


def find_member(detail: JavaClassDetail, reference: str) -> JavaMethod | JavaField | None:
    """A method if the reference looks like a signature, otherwise a field by its name."""
    if "(" in reference:
        return find_method(detail.methods, reference)
    for field in detail.fields:
        if reference in [name.strip() for name in field.name.split(",")]:
            return field
    return None


def find_method(methods: list[JavaMethod], signature: str) -> JavaMethod | None:
    """Exact match first, then ignoring spaces. Models sometimes add parameter names
    ("ausleihen(Mitglied m, Buch b)"), so a method name that is unique in the class is accepted too."""
    for method in methods:
        if method.signature == signature:
            return method

    compact = signature.replace(" ", "")
    for method in methods:
        if method.signature.replace(" ", "") == compact:
            return method

    name = signature.split("(")[0].strip()
    same_name = [method for method in methods if method.signature.split("(")[0] == name]
    return same_name[0] if len(same_name) == 1 else None


# --- Code changed: check a linked use case ---


def analyse_use_case(analysis_id: int, scenario, project: Project, use_case_id: str) -> None:
    use_case = next((uc for uc in project.use_cases if uc.id == use_case_id), None)
    if use_case is None:
        raise AnalysisError(f"Use Case {use_case_id} wurde im Projekt nicht gefunden")
    detail = load_class_detail(find_project_dir(project.id), scenario["class_id"])
    if detail is None:
        raise AnalysisError(f"Klasse {scenario['class_id']} wurde im Projekt nicht gefunden")

    prompt = build_code_change_prompt(
        use_case_id=use_case_id,
        use_case_text=use_case.text,
        class_id=scenario["class_id"],
        method_signature=scenario["method_signature"],
        original_code=scenario["original_code"],
        new_code=scenario["new_code"],
        class_source=detail.source,
    )
    answer = ask_model(analysis_id, CODE_CHANGE_SYSTEM_PROMPT, prompt)

    save_proposals(analysis_id, [parse_use_case_proposal(answer, use_case_id, use_case.text)])
    update_analysis(analysis_id, status="done", status_message="", finished_at=now())


def parse_use_case_proposal(answer: str, use_case_id: str, use_case_text: str) -> dict:
    data = extract_json(answer)
    assessment = str(data.get("assessment", "")).strip()
    problem = ""
    if assessment not in USE_CASE_ASSESSMENTS:
        problem = f"Unbekannte Einschätzung '{assessment}', als nicht beurteilbar behandelt"
        assessment = "unclear"

    proposed_text = str(data.get("proposed_text", "")) if assessment == "deviation" else ""
    if assessment == "deviation" and not proposed_text.strip():
        problem = "Abweichung erkannt, aber kein Textvorschlag geliefert"

    return {
        "target": use_case_id,
        "assessment": assessment,
        "reason": str(data.get("reason", "")),
        "requirement_reference": str(data.get("requirement_reference", "")),
        "original_code": use_case_text,
        "proposed_code": proposed_text,
        "reference_problem": problem,
    }


# --- Helpers ---


def extract_json(answer: str) -> dict:
    """Models often wrap the JSON in ```json fences or add a sentence, so take the outermost object."""
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end == -1:
        raise AnalysisError("Antwort des Modells enthält kein JSON")
    try:
        data = json.loads(answer[start : end + 1])
    except json.JSONDecodeError as error:
        raise AnalysisError(f"Antwort des Modells ist kein gültiges JSON: {error}") from error
    if not isinstance(data, dict):
        raise AnalysisError("Antwort des Modells ist kein JSON-Objekt")
    return data


def save_proposals(analysis_id: int, proposals: list[dict]) -> None:
    with connect() as connection:
        connection.executemany(
            "INSERT INTO proposals (analysis_id, target, assessment, reason, requirement_reference, "
            "original_code, proposed_code, reference_problem) "
            "VALUES (:analysis_id, :target, :assessment, :reason, :requirement_reference, "
            ":original_code, :proposed_code, :reference_problem)",
            [{**proposal, "analysis_id": analysis_id} for proposal in proposals],
        )


def update_analysis(analysis_id: int, **columns) -> None:
    assignments = ", ".join(f"{name} = ?" for name in columns)
    with connect() as connection:
        connection.execute(f"UPDATE analyses SET {assignments} WHERE id = ?", (*columns.values(), analysis_id))
