"""Pruefung und Aufbau eines Szenarios aus der Anwendereingabe.

Die Pruefung sammelt alle Befunde, statt beim ersten abzubrechen, damit der
Anwender seine Eingabe in einem Durchgang korrigieren kann. Ein Szenario ohne
Aenderung wird abgewiesen: Die leere Kandidatenmenge, die daraus folgte, liesse
sich als "kein Einfluss" lesen (Konzept 4.13).
"""

from __future__ import annotations

import uuid

from ..domain.artifacts import MethodSignature
from ..domain.baseline import Baseline
from ..domain.ids import ClassId, ScenarioId, UseCaseId
from ..domain.scenario import (
    ChangeKind,
    CodeChange,
    Direction,
    RequirementChange,
    Scenario,
)
from .schemas import ScenarioCreate


class ScenarioInputError(ValueError):
    """Die Eingabe eines Szenarios ist nicht verwendbar."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


def build_scenario(baseline: Baseline, body: ScenarioCreate) -> Scenario:
    problems: list[str] = []
    requirement_changes = _requirement_changes(baseline, body, problems)
    code_changes = _code_changes(baseline, body, problems)

    if body.direction is Direction.REQUIREMENT_TO_CODE:
        if not body.requirement_changes:
            problems.append("Ein Szenario benoetigt mindestens eine Anforderungsaenderung")
        if body.code_changes:
            problems.append("In der Anforderungsrichtung sind keine Codeaenderungen vorgesehen")
    else:
        if not body.code_changes:
            problems.append("Ein Szenario benoetigt mindestens eine Codeaenderung")
        if body.requirement_changes:
            problems.append("In der Gegenrichtung sind keine Anforderungsaenderungen vorgesehen")

    if problems:
        raise ScenarioInputError(problems)

    return Scenario(
        id=ScenarioId(uuid.uuid4().hex[:12]),
        baseline_id=baseline.id,
        title=body.title,
        direction=body.direction,
        requirement_changes=tuple(requirement_changes),
        code_changes=tuple(code_changes),
    )


def _requirement_changes(
    baseline: Baseline, body: ScenarioCreate, problems: list[str]
) -> list[RequirementChange]:
    changes: list[RequirementChange] = []
    seen: set[str] = set()

    for item in body.requirement_changes:
        if item.use_case_id in seen:
            problems.append(
                f"Der Use Case {item.use_case_id} wird mehrfach geaendert; eine "
                "Aenderung je Use Case ist vorgesehen"
            )
            continue
        seen.add(item.use_case_id)

        exists = UseCaseId(item.use_case_id) in baseline.use_cases
        if item.kind is ChangeKind.ADD and exists:
            problems.append(
                f"Die Kennung {item.use_case_id} ist im Ausgangsstand vergeben; ein "
                "neuer Use Case braucht eine eigene Kennung"
            )
            continue
        if item.kind is not ChangeKind.ADD and not exists:
            problems.append(f"Der Use Case {item.use_case_id} existiert im Ausgangsstand nicht")
            continue

        unknown = [c for c in item.manual_class_ids if ClassId(c) not in baseline.classes]
        if unknown:
            problems.append(
                f"Manuelle Zuordnung von {item.use_case_id} nennt unbekannte Klassen: "
                + ", ".join(unknown)
            )
            continue

        try:
            changes.append(
                RequirementChange(
                    kind=item.kind,
                    use_case_id=UseCaseId(item.use_case_id),
                    target_text=item.target_text,
                    manual_class_ids=tuple(
                        dict.fromkeys(ClassId(c) for c in item.manual_class_ids)
                    ),
                )
            )
        except ValueError as error:
            problems.append(f"{item.use_case_id}: {error}")
    return changes


def _code_changes(
    baseline: Baseline, body: ScenarioCreate, problems: list[str]
) -> list[CodeChange]:
    changes: list[CodeChange] = []

    for item in body.code_changes:
        java_class = baseline.java_class(ClassId(item.class_id))
        if java_class is None:
            problems.append(f"Die Klasse {item.class_id} existiert im Ausgangsstand nicht")
            continue

        signature: MethodSignature | None = None
        before = java_class.source
        if item.signature is not None:
            signature = MethodSignature(
                item.signature.name, tuple(item.signature.parameter_types)
            )
            method = java_class.method(signature)
            if method is None:
                reason = (
                    "die Klasse konnte nicht geparst werden"
                    if not java_class.parsed
                    else "die Signatur kommt in der Klasse nicht vor"
                )
                problems.append(f"{item.class_id}#{signature}: {reason}")
                continue
            before = method.source

        changes.append(
            CodeChange(
                class_id=ClassId(item.class_id),
                before=before,
                after=item.after,
                signature=signature,
            )
        )
    return changes
