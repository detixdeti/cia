"""Szenarien und Aenderungsauftraege.

Umsetzung von Konzept Abschnitt 4.2 (Szenariomodell) und 4.8 (Ablaufzustaende).
Ein Szenario verweist auf einen unveraenderlichen Ausgangsstand und veraendert
diesen nie. Es haelt Aenderungsrichtung, Aenderungsart, betroffene
Ausgangsartefakte und den beschriebenen Zielzustand fest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .artifacts import MethodSignature
from .ids import BaselineId, ClassId, ScenarioId, UseCaseId
from .links import TraceLink


class Direction(str, Enum):
    """Analyserichtung."""

    #: Von der Anforderung zum Code (Konzept 4.3).
    REQUIREMENT_TO_CODE = "requirement_to_code"
    #: Von einer Codeaenderung zu den Use Cases (Konzept 4.6).
    CODE_TO_REQUIREMENT = "code_to_requirement"


class ChangeKind(str, Enum):
    """Art der Aenderung an einer Anforderung (Konzept 4.3)."""

    DEACTIVATE = "deactivate"
    MODIFY = "modify"
    ADD = "add"


class ScenarioState(str, Enum):
    """Zustaende eines Szenarios nach Konzept Abschnitt 4.8.

    Der Uebergang nach ``READY_FOR_REVIEW`` bedeutet nicht, dass alle Fragen
    geklaert sind. Offene Faelle bleiben auch danach sichtbar.
    """

    CREATED = "created"
    STRUCTURALLY_CHECKED = "structurally_checked"
    ANALYSIS_RUNNING = "analysis_running"
    READY_FOR_REVIEW = "ready_for_review"
    CLOSED = "closed"
    DISCARDED = "discarded"


#: Erlaubte Zustandsuebergaenge. Ein Abbruch ist aus jedem offenen Zustand
#: zulaessig (Konzept 4.13: der Anwender muss ein Szenario verwerfen koennen,
#: ohne einen vollstaendigen Soll-Zustand zu erzeugen).
_TRANSITIONS: dict[ScenarioState, frozenset[ScenarioState]] = {
    ScenarioState.CREATED: frozenset(
        {ScenarioState.STRUCTURALLY_CHECKED, ScenarioState.DISCARDED}
    ),
    ScenarioState.STRUCTURALLY_CHECKED: frozenset(
        {ScenarioState.ANALYSIS_RUNNING, ScenarioState.DISCARDED}
    ),
    ScenarioState.ANALYSIS_RUNNING: frozenset(
        {
            ScenarioState.READY_FOR_REVIEW,
            ScenarioState.STRUCTURALLY_CHECKED,
            ScenarioState.DISCARDED,
        }
    ),
    ScenarioState.READY_FOR_REVIEW: frozenset(
        {
            ScenarioState.ANALYSIS_RUNNING,
            ScenarioState.CLOSED,
            ScenarioState.DISCARDED,
        }
    ),
    ScenarioState.CLOSED: frozenset(),
    ScenarioState.DISCARDED: frozenset(),
}


class IllegalTransition(RuntimeError):
    """Ein unzulaessiger Zustandsuebergang."""


@dataclass(frozen=True, slots=True)
class RequirementChange:
    """Eine geplante Aenderung an genau einem Use Case."""

    kind: ChangeKind
    use_case_id: UseCaseId
    #: Nur bei MODIFY und ADD gesetzt: der vom Anwender formulierte Zieltext.
    target_text: str | None = None
    #: Nur bei ADD: die manuell ausgewaehlten Klassen. Konzept 4.3 schliesst
    #: aus, dass das LLM hierfuer Klassen vorschlaegt.
    manual_class_ids: tuple[ClassId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.kind is ChangeKind.MODIFY and not self.target_text:
            raise ValueError("Eine Aenderung benoetigt einen Zieltext")
        if self.kind is ChangeKind.ADD and not self.target_text:
            raise ValueError("Ein neuer Use Case benoetigt einen Text")
        if self.kind is not ChangeKind.ADD and self.manual_class_ids:
            raise ValueError(
                "Manuelle Zuordnungen sind nur fuer neue Use Cases vorgesehen"
            )

    def scenario_links(self) -> tuple[TraceLink, ...]:
        from .links import LinkOrigin

        return tuple(
            TraceLink(self.use_case_id, cid, LinkOrigin.SCENARIO)
            for cid in self.manual_class_ids
        )


@dataclass(frozen=True, slots=True)
class CodeChange:
    """Eine manuell eingegebene Codeaenderung (Konzept 4.6).

    Der Prototyp enthaelt keine Git-Anbindung. Die Ausgangsfassung stammt aus
    dem Import, die geaenderte Fassung gibt der Anwender ein.
    """

    class_id: ClassId
    before: str
    after: str
    #: Bei einer Methodenaenderung bleibt die Zugehoerigkeit zur Klasse
    #: erhalten, damit deren Trace-Links die Kandidaten bestimmen.
    signature: MethodSignature | None = None

    @property
    def is_method_level(self) -> bool:
        return self.signature is not None


@dataclass(slots=True)
class Scenario:
    """Ein Aenderungsszenario auf einem festen Ausgangsstand."""

    id: ScenarioId
    baseline_id: BaselineId
    title: str
    direction: Direction
    requirement_changes: tuple[RequirementChange, ...] = ()
    code_changes: tuple[CodeChange, ...] = ()
    state: ScenarioState = ScenarioState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.direction is Direction.REQUIREMENT_TO_CODE and self.code_changes:
            raise ValueError(
                "In der Anforderungsrichtung sind keine Codeaenderungen vorgesehen"
            )
        if self.direction is Direction.CODE_TO_REQUIREMENT and self.requirement_changes:
            raise ValueError(
                "In der Gegenrichtung sind keine Anforderungsaenderungen vorgesehen"
            )

    def transition_to(self, new_state: ScenarioState) -> None:
        allowed = _TRANSITIONS[self.state]
        if new_state not in allowed:
            raise IllegalTransition(
                f"Uebergang {self.state.value} -> {new_state.value} ist nicht zulaessig"
            )
        self.state = new_state

    @property
    def changed_use_case_ids(self) -> frozenset[UseCaseId]:
        return frozenset(c.use_case_id for c in self.requirement_changes)

    @property
    def changed_class_ids(self) -> frozenset[ClassId]:
        return frozenset(c.class_id for c in self.code_changes)

    @property
    def scenario_links(self) -> tuple[TraceLink, ...]:
        """Alle manuell im Szenario festgelegten Zuordnungen."""
        return tuple(
            link for change in self.requirement_changes for link in change.scenario_links()
        )
