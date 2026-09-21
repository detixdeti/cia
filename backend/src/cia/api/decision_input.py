"""Pruefung und Aufbau einer Entscheidung aus der Anwendereingabe (F5).

Regeln (Konzept 4.6, 4.7 und 4.10):
- Entschieden werden nur Aenderungsvorschlaege des Modells (in der
  Gegenrichtung: eine moegliche Abweichung).
- Einen Vorschlag mit Problem (unbekannte Methode, unvollstaendig, doppelt,
  in der Gegenrichtung ohne Textvorschlag) kann der Anwender verwerfen oder
  zurueckstellen, aber nicht annehmen. Ein ungueltiger Eintrag wird nicht
  stillschweigend uebernommen.
- Eine Ueberarbeitung gehoert zu einer Annahme. Sie ersetzt den Vorschlag des
  Modells nicht, sondern steht daneben.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain.decision import Decision, DecisionKind
from ..domain.scenario import Scenario
from ..llm.answer import Status
from ..llm.backward import CodeChangeRun, DeviationStatus
from ..llm.run import AnalysisRun, AnyRun
from .schemas import DecisionIn


class DecisionInputError(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass(frozen=True, slots=True)
class Suggestion:
    """Ein Eintrag der Modellantwort, auf den sich eine Entscheidung bezieht.

    Der Typ vereinheitlicht beide Richtungen, damit die Pruefung nicht zwischen
    ihnen unterscheiden muss.
    """

    #: Methode oder Klassenstelle (Anforderungsrichtung), Use Case (Gegenrichtung).
    target: str
    #: Vorschlag des Modells, falls vorhanden.
    proposal: str | None
    #: Ob es ein Vorschlag ist, ueber den entschieden werden kann.
    is_proposal: bool
    #: Gruende, die eine Annahme verhindern. Leer heisst: annehmbar.
    blockers: tuple[str, ...]


def find_suggestion(run: AnyRun, subject_id: str, entry_index: int) -> Suggestion | None:
    if isinstance(run, AnalysisRun):
        return _forward_suggestion(run, subject_id, entry_index)
    return _backward_suggestion(run, subject_id, entry_index)


def _forward_suggestion(run: AnalysisRun, class_id: str, entry_index: int) -> Suggestion | None:
    for result in run.results:
        if result.class_id == class_id and result.analysis is not None:
            entries = result.analysis.answer.entries
            if 0 <= entry_index < len(entries):
                checked = entries[entry_index]
                return Suggestion(
                    target=checked.entry.target,
                    proposal=checked.entry.proposal,
                    is_proposal=checked.entry.status is Status.CHANGE_PROPOSED,
                    blockers=tuple(p.value for p in checked.problems),
                )
    return None


def _backward_suggestion(
    run: CodeChangeRun, use_case_id: str, entry_index: int
) -> Suggestion | None:
    # Je Use Case gibt es genau eine Einschaetzung.
    if entry_index != 0:
        return None
    for analysis in run.results:
        if analysis.use_case_id != use_case_id:
            continue
        assessment = analysis.answer.assessment
        if assessment is None:
            # Antwort nicht lesbar: nichts, worueber man entscheiden koennte.
            return Suggestion(use_case_id, None, False, ())
        blockers = [p.value for p in analysis.answer.assessment_problems]
        if not assessment.proposed_text:
            blockers.append("no_proposed_text")
        return Suggestion(
            target=use_case_id,
            proposal=assessment.proposed_text,
            is_proposal=assessment.status is DeviationStatus.POSSIBLE_DEVIATION,
            blockers=tuple(blockers),
        )
    return None


def build_decision(scenario: Scenario, runs: list[AnyRun], body: DecisionIn) -> Decision:
    run = next((r for r in runs if r.run_id == body.run_id), None)
    if run is None:
        raise DecisionInputError([f"Lauf {body.run_id} gehoert nicht zu diesem Szenario"])

    suggestion = find_suggestion(run, body.subject_id, body.entry_index)
    if suggestion is None:
        raise DecisionInputError(
            [f"Im Lauf {body.run_id} gibt es zu {body.subject_id} keinen Eintrag {body.entry_index}"]
        )

    problems: list[str] = []
    if not suggestion.is_proposal:
        problems.append("Entschieden werden nur Aenderungsvorschlaege des Modells")
    if body.kind is DecisionKind.ACCEPTED and suggestion.blockers:
        genannt = ", ".join(suggestion.blockers)
        problems.append(f"Ein Vorschlag mit Problemen kann nicht angenommen werden: {genannt}")

    revised = body.revised_proposal.strip() if body.revised_proposal else None
    if body.revised_proposal is not None and not revised:
        problems.append("Die Ueberarbeitung ist leer")
    if revised and body.kind is not DecisionKind.ACCEPTED:
        problems.append("Eine Ueberarbeitung gehoert zu einer Annahme")

    if problems:
        raise DecisionInputError(problems)

    return Decision(
        decision_id=uuid.uuid4().hex[:12],
        scenario_id=scenario.id,
        run_id=body.run_id,
        subject_id=body.subject_id,
        entry_index=body.entry_index,
        kind=body.kind,
        revised_proposal=revised,
        decided_at=datetime.now(timezone.utc),
    )
