"""Einlesen der Trace-Link-Datei.

Das Format ist in Konzept Abschnitt 4.2 festgelegt: Jede Zeile enthaelt genau
eine Zuordnung der Form ``UC1 -> Person.java``. Links vom Pfeil steht die
Use-Case-Kennung, rechts der Dateiname der zugeordneten Klasse. Mehrere
Zuordnungen zu einem Use Case entstehen durch Wiederholung seiner Kennung in
weiteren Zeilen. Die Datei enthaelt weder Metadaten noch Versionsangaben oder
Relationstypen.

Das genaue Format der Datei des Lehrstuhls steht noch aus. Der Parser ist
deshalb bewusst eng: Er akzeptiert die dokumentierte Form und weist alles
andere als Befund aus, statt zu raten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.ids import ClassId, UseCaseId
from ..domain.links import LinkOrigin, TraceLink
from .result import Diagnostics, DiagnosticCode, Severity

#: Eine Zuordnungszeile. Der Pfeil wird in den Schreibweisen ``->`` und ``-->``
#: akzeptiert, umgebende Leerzeichen sind beliebig.
_LINK_PATTERN = re.compile(r"^\s*(?P<uc>[^\s>-][^\s]*)\s*-{1,2}>\s*(?P<cls>\S+)\s*$")

#: Zeilen, die vollstaendig uebersprungen werden.
_COMMENT_PREFIXES = ("#", "//")


@dataclass(frozen=True, slots=True)
class TraceLinkFile:
    """Das Ergebnis des Einlesens.

    ``links`` enthaelt die eindeutigen Zuordnungen, ``read_lines`` die Zahl der
    verarbeiteten Zuordnungszeilen. Konzept 4.13 verlangt, beide Zahlen
    auseinanderzuhalten.
    """

    links: tuple[TraceLink, ...]
    read_lines: int
    duplicate_lines: int

    @property
    def unique_link_count(self) -> int:
        return len(self.links)


def parse_trace_links(
    content: str,
    diagnostics: Diagnostics,
    source_file: str = "tracelinks.txt",
) -> TraceLinkFile:
    """Liest den Inhalt einer Trace-Link-Datei.

    Der Aufruf pruefte noch nicht, ob die genannten Kennungen im Projektstand
    vorhanden sind. Diese Aufloesung geschieht getrennt in
    :mod:`cia.importing.project`, weil Konzept 4.2 die technische
    Aufloesbarkeit von der fachlichen Gueltigkeit der Links trennt.
    """
    seen: set[tuple[UseCaseId, ClassId]] = set()
    links: list[TraceLink] = []
    read_lines = 0
    duplicates = 0

    for number, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(_COMMENT_PREFIXES):
            continue

        match = _LINK_PATTERN.match(stripped)
        if match is None:
            diagnostics.add(
                DiagnosticCode.MALFORMED_LINE,
                Severity.ERROR,
                f"Zeile entspricht nicht dem Format 'UC -> Datei.java': {stripped!r}",
                source_file,
                number,
            )
            continue

        read_lines += 1
        use_case_id = UseCaseId(match.group("uc"))
        class_id = ClassId(match.group("cls"))
        key = (use_case_id, class_id)

        if key in seen:
            duplicates += 1
            # Konzept 4.2: Doppelte identische Zuordnungen koennen
            # zusammengefasst werden, ohne daraus zusaetzliche Evidenz
            # abzuleiten.
            diagnostics.add(
                DiagnosticCode.DUPLICATE_LINK,
                Severity.INFO,
                f"Zuordnung {use_case_id} -> {class_id} war bereits deklariert",
                source_file,
                number,
            )
            continue

        seen.add(key)
        links.append(TraceLink(use_case_id, class_id, LinkOrigin.IMPORTED))

    return TraceLinkFile(
        links=tuple(links),
        read_lines=read_lines,
        duplicate_lines=duplicates,
    )
