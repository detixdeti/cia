"""Einlesen der Use-Case-Texte.

Das Format der Anforderungen des Lehrstuhls steht noch aus. Bis dahin liest der
Import eine Textdatei je Use Case. Die Kennung stammt aus der Ueberschrift oder,
falls diese fehlt, aus dem Dateinamen. Konzept 4.2 verlangt eine stabile
Kennung; der Dateiname als Rueckfallebene erfuellt das, solange er nicht
geaendert wird.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..domain.artifacts import UseCase
from ..domain.ids import BaselineId, UseCaseId
from .result import Diagnostics, DiagnosticCode, Severity

#: ``# UC1: Buch ausleihen``, ``# UC1 Buch ausleihen`` oder ``# UC1``.
#: Die Kennung darf keinen Doppelpunkt enthalten, damit sie am Trennzeichen
#: endet. Ein nicht gieriges Muster wuerde hier bereits nach dem ersten Zeichen
#: abbrechen und ``U`` als Kennung liefern.
_HEADING_PATTERN = re.compile(r"^#\s*(?P<id>[^\s:]+)\s*(?:[:\-]\s*)?(?P<title>.*)$")


def parse_use_case(
    path: Path,
    content: str,
    baseline_id: BaselineId,
    diagnostics: Diagnostics,
) -> UseCase:
    """Liest einen einzelnen Use Case."""
    lines = content.splitlines()
    use_case_id = UseCaseId(path.stem)
    title = path.stem
    body_start = 0

    for index, line in enumerate(lines):
        if not line.strip():
            continue
        match = _HEADING_PATTERN.match(line.strip())
        if match:
            use_case_id = UseCaseId(match.group("id"))
            title = match.group("title").strip() or path.stem
            body_start = index + 1
        break

    text = "\n".join(lines[body_start:]).strip()
    if not text:
        # Konzept 4.13: Eine fehlende Eingabe muss als solche erkennbar sein
        # und darf nicht als unauffaelliger Befund erscheinen.
        diagnostics.add(
            DiagnosticCode.EMPTY_USE_CASE_TEXT,
            Severity.WARNING,
            f"Use Case {use_case_id} enthaelt keinen Text",
            path.name,
        )

    return UseCase(
        id=use_case_id,
        baseline_id=baseline_id,
        title=title,
        text=text,
        source_file=path.name,
    )


def load_use_cases(
    directory: Path,
    baseline_id: BaselineId,
    diagnostics: Diagnostics,
    patterns: tuple[str, ...] = ("*.md", "*.txt"),
) -> dict[UseCaseId, UseCase]:
    """Liest alle Use-Case-Dateien eines Verzeichnisses."""
    files: list[tuple[str, str]] = []
    for pattern in patterns:
        for path in sorted(directory.glob(pattern)):
            files.append((path.name, path.read_text(encoding="utf-8")))
    return use_cases_from_texts(files, baseline_id, diagnostics)


def use_cases_from_texts(
    files: list[tuple[str, str]],
    baseline_id: BaselineId,
    diagnostics: Diagnostics,
) -> dict[UseCaseId, UseCase]:
    """Liest Use Cases aus Dateiname und Inhalt.

    Der Weg fuer Import von der Platte und fuer Upload ist derselbe.
    """
    result: dict[UseCaseId, UseCase] = {}

    for name, content in files:
        path = Path(name)
        use_case = parse_use_case(path, content, baseline_id, diagnostics)
        if use_case.id in result:
            previous = result[use_case.id].source_file
            diagnostics.add(
                DiagnosticCode.AMBIGUOUS_USE_CASE,
                Severity.ERROR,
                (
                    f"Use-Case-Kennung {use_case.id} ist mehrfach vergeben: "
                    f"{previous} und {path.name}"
                ),
                path.name,
            )
            continue
        result[use_case.id] = use_case

    return result
