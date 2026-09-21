"""Schnittstelle zum Sprachmodell.

Der Zugang zum Modell ist noch nicht geklaert. Deshalb kennt der Rest des
Systems nur diese kleine Schnittstelle: Text hinein, Text heraus. Ein echter
Anbieter oder der Mock (mock.py) lassen sich austauschen, ohne dass sich
sonst etwas aendert.
"""

from __future__ import annotations

from typing import Protocol


class LlmError(Exception):
    """Die Anfrage ans Modell ist gescheitert, z. B. durch Zeitueberschreitung."""


class LlmProvider(Protocol):
    #: Kennung des Modells oder Anbieters, wird protokolliert (Konzept 4.13).
    name: str
    #: Generierungseinstellungen, z. B. Temperatur. Werden mit protokolliert.
    #: Beim Mock leer.
    settings: dict[str, str | int | float]

    def complete(self, prompt: str) -> str:
        """Schickt den Prompt ans Modell und gibt dessen Antworttext zurueck.

        Bei einem Fehler wird ``LlmError`` ausgeloest.
        """
        ...
