"""Ergebnistyp des Imports.

Konzept Abschnitt 4.2 verlangt, unaufloesbare Zuordnungen mit einer
Fehlermeldung auszuweisen. Ein Importfehler darf die uebrige Verarbeitung nicht
abbrechen, weil der Anwender sonst nicht erfaehrt, welche Artefakte in Ordnung
waren. Deshalb sammelt der Import Befunde, statt Ausnahmen auszuloesen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Severity(str, Enum):
    """Schweregrad eines Importbefunds.

    ``ERROR`` bedeutet, dass die betroffene Angabe nicht verwendet werden kann.
    ``WARNING`` bedeutet, dass sie verwendet wird, aber einer Klaerung bedarf.
    ``INFO`` haelt eine Beobachtung fest, die fuer die Abdeckungsanzeige
    relevant ist.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DiagnosticCode(str, Enum):
    """Kennungen der Importbefunde.

    Sie werden getrennt von ihrem Text gefuehrt, damit sich Haeufigkeiten fuer
    Kapitel 6 auszaehlen lassen, ohne Meldungstexte zu vergleichen.
    """

    MALFORMED_LINE = "malformed_line"
    UNKNOWN_USE_CASE = "unknown_use_case"
    UNKNOWN_CLASS = "unknown_class"
    AMBIGUOUS_CLASS = "ambiguous_class"
    AMBIGUOUS_USE_CASE = "ambiguous_use_case"
    DUPLICATE_LINK = "duplicate_link"
    PARSE_FAILED = "parse_failed"
    EMPTY_USE_CASE_TEXT = "empty_use_case_text"
    UNLINKED_CLASS = "unlinked_class"
    UNLINKED_USE_CASE = "unlinked_use_case"
    #: Beim Upload mitgeschickte Datei, die nicht zum Import gehoert.
    IGNORED_FILE = "ignored_file"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Ein einzelner Befund mit seiner Herkunft."""

    code: DiagnosticCode
    severity: Severity
    message: str
    source_file: str | None = None
    line_number: int | None = None

    def __str__(self) -> str:
        where = ""
        if self.source_file:
            where = f" [{self.source_file}"
            where += f":{self.line_number}]" if self.line_number else "]"
        return f"{self.severity.value}: {self.message}{where}"


@dataclass(slots=True)
class Diagnostics:
    """Sammlung von Befunden."""

    entries: list[Diagnostic] = field(default_factory=list)

    def add(
        self,
        code: DiagnosticCode,
        severity: Severity,
        message: str,
        source_file: str | None = None,
        line_number: int | None = None,
    ) -> None:
        self.entries.append(
            Diagnostic(code, severity, message, source_file, line_number)
        )

    def extend(self, others: Iterable[Diagnostic]) -> None:
        self.entries.extend(others)

    def of(self, code: DiagnosticCode) -> list[Diagnostic]:
        return [d for d in self.entries if d.code is code]

    def by_severity(self, severity: Severity) -> list[Diagnostic]:
        return [d for d in self.entries if d.severity is severity]

    @property
    def has_errors(self) -> bool:
        return any(d.severity is Severity.ERROR for d in self.entries)

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for d in self.entries:
            result[d.code.value] = result.get(d.code.value, 0) + 1
        return result

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)
