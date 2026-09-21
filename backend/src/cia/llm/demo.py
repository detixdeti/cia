"""Demo-Anbieter: Beispielantworten fuer Vorfuehrungen ohne echtes Modell.

Der normale Mock (mock.py) bewertet nichts. Damit laesst sich die Oberflaeche
nicht vorfuehren, weil nie ein Vorschlag erscheint. Dieser Anbieter liefert
deshalb feste Beispielantworten, damit Vorschlaege, Ist-Soll-Vergleich und
Entscheidungen sichtbar werden.

Jede Antwort ist ausdruecklich mit "[DEMO]" gekennzeichnet. Es ist keine
Bewertung des Codes und kein Ergebnis der Arbeit. Er darf nie fuer Messungen
oder die Nutzerstudie verwendet werden.
"""

from __future__ import annotations

import json
import re

_METHOD_LINE = re.compile(r"^### (.+)$", re.MULTILINE)
_USE_CASE_LINE = re.compile(r"^USE CASE: (\S+)", re.MULTILINE)


class DemoProvider:
    name = "demo"

    def __init__(self) -> None:
        self.settings: dict[str, str | int | float] = {}

    def complete(self, prompt: str) -> str:
        if "\nKLASSE: " in prompt:
            return json.dumps(_class_answer(prompt))
        return json.dumps(_use_case_answer(prompt))


def _class_answer(prompt: str) -> dict:
    """Anforderungsrichtung: erste Methode Vorschlag, zweite kein Bedarf,
    dritte nicht beurteilbar. Zu allen weiteren sagt die Demo nichts."""
    methods = _METHOD_LINE.findall(prompt)
    entries = []

    if len(methods) >= 1:
        entries.append(
            {
                "target_kind": "method",
                "target": methods[0],
                "status": "change_proposed",
                "use_case_passage": "[DEMO] betroffene Stelle im Use-Case-Text",
                "reason": "[DEMO] Beispielbegruendung. Das ist keine echte Bewertung.",
                "proposal": "[DEMO] Hier stuende der vorgeschlagene Soll-Zustand der Methode.",
            }
        )
    if len(methods) >= 2:
        entries.append(
            {
                "target_kind": "method",
                "target": methods[1],
                "status": "no_change_visible",
                "use_case_passage": "",
                "reason": "[DEMO] Beispiel: im Kontext nichts erkennbar.",
                "proposal": None,
            }
        )
    if len(methods) >= 3:
        entries.append(
            {
                "target_kind": "method",
                "target": methods[2],
                "status": "not_assessable",
                "use_case_passage": "",
                "reason": "[DEMO] Beispiel: Aufrufer der Methode fehlen im Kontext.",
                "proposal": None,
            }
        )

    return {
        "entries": entries,
        "assumptions": ["[DEMO] Beispielannahme"],
        "missing_context": ["[DEMO] Beispiel fuer fehlenden Kontext"],
    }


def _use_case_answer(prompt: str) -> dict:
    """Gegenrichtung: Die Einschaetzung haengt von der Use-Case-Kennung ab,
    damit die Beispiele nicht alle gleich aussehen."""
    match = _USE_CASE_LINE.search(prompt)
    use_case_id = match.group(1) if match else ""
    status = ("possible_deviation", "no_deviation_visible", "insufficient_information")[
        sum(ord(c) for c in use_case_id) % 3
    ]

    if status == "possible_deviation":
        return {
            "status": status,
            "affected_passage": "[DEMO] Erfolgsbedingung",
            "reason": "[DEMO] Beispielbegruendung. Das ist keine echte Bewertung.",
            "proposed_text": "[DEMO] Hier stuende ein vorgeschlagener neuer Use-Case-Text.",
            "assumptions": ["[DEMO] Beispielannahme"],
            "missing_context": [],
        }
    return {
        "status": status,
        "affected_passage": "",
        "reason": "[DEMO] Beispiel: keine Bewertung.",
        "proposed_text": None,
        "assumptions": [],
        "missing_context": ["[DEMO] Beispiel fuer fehlenden Kontext"] if status != "no_deviation_visible" else [],
    }
