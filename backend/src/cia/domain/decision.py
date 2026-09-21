"""Entscheidungen des Anwenders zu Modellvorschlaegen.

Umsetzung von Konzept Abschnitt 4.6 und 4.11 (F5). Das Werkzeug schlaegt vor,
der Mensch entscheidet. Eine Entscheidung veraendert weder den Modellvorschlag
noch Dateien des Projekts.

Entscheidungen werden nur angehaengt, nie geaendert. Aendert der Anwender seine
Meinung, entsteht ein neuer Eintrag. So bleibt in der Auswertung sichtbar, was
das Modell vorgeschlagen, was der Anwender ueberarbeitet und wie er zuletzt
entschieden hat (Konzept 4.13).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .ids import ScenarioId


class DecisionKind(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    #: Zurueckgestellt: noch nicht entschieden. Bleibt ein offener Fall
    #: (Konzept 4.6).
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class Decision:
    decision_id: str
    scenario_id: ScenarioId
    #: Der Vorschlag, um den es geht: Lauf, Gegenstand und Nummer des Eintrags.
    #: Der Gegenstand ist in der Anforderungsrichtung eine Klasse und in der
    #: Gegenrichtung ein Use Case. Dort gibt es je Use Case genau eine
    #: Einschaetzung, die Nummer ist dann immer 0. Der Vorschlag selbst wird
    #: nicht kopiert.
    run_id: str
    subject_id: str
    entry_index: int
    kind: DecisionKind
    #: Vom Anwender ueberarbeiteter Soll-Zustand. Der urspruengliche Vorschlag
    #: des Modells bleibt unveraendert daneben stehen (Konzept 4.6).
    revised_proposal: str | None
    decided_at: datetime

    @property
    def suggestion_key(self) -> tuple[str, str, int]:
        return (self.run_id, self.subject_id, self.entry_index)


def current_decisions(history: list[Decision]) -> list[Decision]:
    """Die jeweils letzte Entscheidung zu jedem Vorschlag."""
    latest: dict[tuple[str, str, int], Decision] = {}
    for decision in history:
        latest[decision.suggestion_key] = decision
    return list(latest.values())
