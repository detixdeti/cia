"""Mock-Anbieter, damit die Pipeline ohne API-Key laeuft und testbar bleibt."""

from __future__ import annotations

#: Vorgabe fuer den laufenden Prototyp, solange kein echtes Modell angebunden ist.
#: Sie bewertet bewusst nichts und ist fuer beide Richtungen lesbar:
#: - Anforderungsrichtung: keine Eintraege, alle Methoden bleiben offen.
#: - Gegenrichtung: "insufficient_information", der Use Case bleibt offen.
#: Der Mock taeuscht so keine Beurteilung vor (Konzept 4.5).
ANTWORT_OHNE_BEWERTUNG = (
    '{"entries": [], "status": "insufficient_information", '
    '"affected_passage": "", "reason": "Mock-Anbieter: keine echte Bewertung", '
    '"proposed_text": null, '
    '"assumptions": ["Mock-Anbieter: keine echte Bewertung"], '
    '"missing_context": ["Es ist kein echtes Modell angebunden"]}'
)


class MockProvider:
    """Antwortet immer mit demselben Text und merkt sich alle Anfragen."""

    name = "mock"

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.settings: dict[str, str | int | float] = {}
        #: Alle Prompts, die der Mock bekommen hat. Praktisch zum Pruefen.
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answer
