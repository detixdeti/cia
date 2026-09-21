"""Abdeckungsanzeige und offene Faelle eines Szenarios.

Umsetzung von Konzept Abschnitt 4.12 (und 4.8 fuer den Abschluss). Die Zahlen
dienen der Transparenz des Ablaufs, nicht als Qualitaetsnachweis. Sie zeigen,
wie weit ein Lauf gekommen ist und was offen bleibt.

Vier Zustaende sind ausdruecklich getrennt, weil sie verschiedene Ursachen und
verschiedene naechste Schritte haben. Keiner davon gilt als Entwarnung:

- nicht zugeordnet       Eine Aenderung hat keine Klasse (``NOT_ASSIGNED``).
- nicht verarbeitet      Eine Klasse konnte nicht aufbereitet oder vom Modell
                         nicht lesbar beantwortet werden (``NOT_PROCESSED``).
- nicht beurteilbar      Das Modell sagt "nicht beurteilbar" oder nichts zu einer
                         Methode (``NOT_ASSESSABLE``, ``UNANSWERED_METHOD``).
- kein Bedarf erkennbar  Nur "im betrachteten Kontext". Wird gezaehlt, ist aber
                         kein offener Fall und keine Garantie.

Dieses Modul rechnet nur. Es fragt kein Modell und aendert nichts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..domain.baseline import Baseline
from ..domain.decision import Decision, DecisionKind, current_decisions
from ..llm.answer import AnswerState, Status
from ..llm.backward import CodeChangeRun, DeviationStatus
from ..llm.run import AnalysisRun


class OpenKind(str, Enum):
    NOT_ASSIGNED = "not_assigned"
    NOT_PROCESSED = "not_processed"
    NOT_ASSESSABLE = "not_assessable"
    UNANSWERED_METHOD = "unanswered_method"
    #: Ein Eintrag ohne Aenderungsvorschlag, der aber ein Problem hat.
    ENTRY_WITH_PROBLEM = "entry_with_problem"
    PROPOSAL_UNDECIDED = "proposal_undecided"
    PROPOSAL_DEFERRED = "proposal_deferred"


@dataclass(frozen=True, slots=True)
class OpenItem:
    kind: OpenKind
    #: Worauf sich der Fall bezieht, z. B. ``UC6`` oder ``Katalog.java#suche(String)``.
    ref: str
    detail: str


@dataclass(frozen=True, slots=True)
class Coverage:
    run_id: str
    #: Zaehlwerte, getrennt nach Stufen (Konzept 4.12): importiert,
    #: strukturell zugeordnet, aufbereitet, analysiert.
    counts: dict[str, int]
    open_items: tuple[OpenItem, ...]


@dataclass(frozen=True, slots=True)
class Closure:
    """Der Abschluss eines Szenarios (Konzept 4.8).

    Auch nach dem Abschluss bleibt sichtbar, welche Fragen nicht geklaert
    wurden: ``open_items`` haelt den Stand im Moment des Abschlusses fest.
    """

    run_id: str
    closed_at: datetime
    #: Ob der Anwender die offenen Faelle ausdruecklich zur Kenntnis genommen hat.
    open_items_acknowledged: bool
    #: Begruendung des Anwenders fuer den Abschluss trotz offener Faelle.
    note: str | None
    open_items: tuple[OpenItem, ...]


def compute_coverage(
    baseline: Baseline, run: AnalysisRun, decisions: list[Decision]
) -> Coverage:
    """Berechnet Zaehlwerte und offene Faelle fuer einen Lauf."""
    # Nur die jeweils letzte Entscheidung je Vorschlag zaehlt.
    current = {
        d.suggestion_key: d for d in current_decisions(decisions) if d.run_id == run.run_id
    }

    counts = {
        "imported_classes": len(baseline.classes),
        "candidate_classes": len(run.results),
        "prepared_classes": 0,
        "analyzed_classes": 0,
        "unanswered_methods": 0,
        "not_assessable": 0,
        "no_change_visible": 0,
        "proposals": 0,
        "proposals_accepted": 0,
        "proposals_rejected": 0,
        "proposals_deferred": 0,
        "proposals_undecided": 0,
    }
    items: list[OpenItem] = []

    for change in run.unresolved:
        items.append(OpenItem(OpenKind.NOT_ASSIGNED, change.use_case_id, change.reason))

    for result in run.results:
        class_id = result.class_id
        if result.analysis is None:
            items.append(OpenItem(OpenKind.NOT_PROCESSED, class_id, result.not_processed_reason or ""))
            continue

        counts["prepared_classes"] += 1
        answer = result.analysis.answer
        if answer.state is not AnswerState.ANSWERED:
            items.append(OpenItem(OpenKind.NOT_PROCESSED, class_id, "; ".join(answer.problems)))
            continue

        counts["analyzed_classes"] += 1

        for method_ref in answer.unanswered_methods:
            counts["unanswered_methods"] += 1
            items.append(
                OpenItem(
                    OpenKind.UNANSWERED_METHOD,
                    f"{class_id}#{method_ref.signature}",
                    "Das Modell sagt nichts zu dieser Methode",
                )
            )

        for index, checked in enumerate(answer.entries):
            entry = checked.entry
            ref = f"{class_id}: {entry.target}"
            problems = ", ".join(p.value for p in checked.problems)

            if entry.status is Status.CHANGE_PROPOSED:
                counts["proposals"] += 1
                item = _proposal_state(counts, current.get((run.run_id, class_id, index)), ref, problems)
                if item is not None:
                    items.append(item)
            elif problems:
                # Ein Eintrag mit Problem ist keine gueltige Beurteilung. Er wird
                # weder als "nicht beurteilbar" noch als "kein Bedarf erkennbar"
                # gezaehlt, sondern bleibt als Problem offen.
                items.append(OpenItem(OpenKind.ENTRY_WITH_PROBLEM, ref, problems))
            elif entry.status is Status.NOT_ASSESSABLE:
                counts["not_assessable"] += 1
                items.append(OpenItem(OpenKind.NOT_ASSESSABLE, ref, entry.reason))
            else:
                counts["no_change_visible"] += 1

    return Coverage(run_id=run.run_id, counts=counts, open_items=tuple(items))


def compute_backward_coverage(
    baseline: Baseline, run: CodeChangeRun, decisions: list[Decision]
) -> Coverage:
    """Wie ``compute_coverage``, fuer die Gegenrichtung (Konzept 4.7).

    Die Stufen zaehlen Use Cases statt Klassen. Eine moegliche Abweichung zaehlt
    als Vorschlag, ueber den der Anwender entscheidet.
    """
    current = {
        d.suggestion_key: d for d in current_decisions(decisions) if d.run_id == run.run_id
    }
    counts = {
        "imported_use_cases": len(baseline.use_cases),
        "candidate_use_cases": len(run.results),
        "unassignable_classes": len(run.unassignable_class_ids),
        "analyzed_use_cases": 0,
        "insufficient_information": 0,
        "no_deviation_visible": 0,
        "proposals": 0,
        "proposals_accepted": 0,
        "proposals_rejected": 0,
        "proposals_deferred": 0,
        "proposals_undecided": 0,
    }
    items: list[OpenItem] = []

    for class_id in run.unassignable_class_ids:
        items.append(
            OpenItem(OpenKind.NOT_ASSIGNED, class_id, "Geaenderte Klasse ohne deklarierte Zuordnung")
        )

    for analysis in run.results:
        ref = analysis.use_case_id
        answer = analysis.answer
        if answer.assessment is None:
            items.append(OpenItem(OpenKind.NOT_PROCESSED, ref, "; ".join(answer.problems)))
            continue

        counts["analyzed_use_cases"] += 1
        status = answer.assessment.status
        if status is DeviationStatus.POSSIBLE_DEVIATION:
            counts["proposals"] += 1
            problems = ", ".join(p.value for p in answer.assessment_problems)
            decision = current.get((run.run_id, ref, 0))
            item = _proposal_state(counts, decision, ref, problems)
            if item is not None:
                items.append(item)
        elif status is DeviationStatus.INSUFFICIENT_INFORMATION:
            counts["insufficient_information"] += 1
            detail = "; ".join(answer.missing_context) or answer.assessment.reason
            items.append(OpenItem(OpenKind.NOT_ASSESSABLE, ref, detail))
        else:
            counts["no_deviation_visible"] += 1

    return Coverage(run_id=run.run_id, counts=counts, open_items=tuple(items))


def _proposal_state(
    counts: dict[str, int], decision: Decision | None, ref: str, problems: str
) -> OpenItem | None:
    """Zaehlt den Stand eines Vorschlags. Gibt einen offenen Fall zurueck, falls er offen ist."""
    detail = f"Probleme: {problems}" if problems else "Noch nicht entschieden"

    if decision is None:
        counts["proposals_undecided"] += 1
        return OpenItem(OpenKind.PROPOSAL_UNDECIDED, ref, detail)
    if decision.kind is DecisionKind.DEFERRED:
        counts["proposals_deferred"] += 1
        return OpenItem(OpenKind.PROPOSAL_DEFERRED, ref, "Zurueckgestellt")
    if decision.kind is DecisionKind.ACCEPTED:
        counts["proposals_accepted"] += 1
    else:
        counts["proposals_rejected"] += 1
    return None
