"""Import eines vollstaendigen Projektstands.

Umsetzung von Konzept Abschnitt 4.2. Der Import ordnet Anforderungen,
Java-Dateien und Linkdatei einem gemeinsamen Ausgangsstand zu. Er prueft, ob die
referenzierten Kennungen vorhanden und eindeutig sind, und weist unaufloesbare
Links mit einer Fehlermeldung aus.

Die fachliche Gueltigkeit der Links wird als Eingabevoraussetzung behandelt und
von ihrer technischen Aufloesbarkeit getrennt. Der Import prueft ausschliesslich
letztere.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..domain.artifacts import JavaClass
from ..domain.baseline import Baseline
from ..domain.ids import BaselineId, ClassId
from ..domain.links import TraceGraph, TraceLink
from ..parsing.java import JavaParser, TreeSitterJavaParser, class_id_for
from .result import Diagnostics, DiagnosticCode, Severity
from .tracelinks import parse_trace_links
from .usecases import use_cases_from_texts


@dataclass(frozen=True, slots=True)
class ImportLayout:
    """Wo der Import die Bestandteile eines Projektstands erwartet."""

    use_case_dir: str = "usecases"
    source_dir: str = "src"
    trace_link_file: str = "tracelinks.txt"


@dataclass(frozen=True, slots=True)
class ImportReport:
    """Ergebnis eines Imports.

    Baseline und Befunde bleiben getrennt, damit ein Fehler die uebrigen
    Artefakte nicht entwertet.
    """

    baseline: Baseline
    diagnostics: Diagnostics
    read_link_lines: int
    duplicate_link_lines: int

    def summary(self) -> dict[str, object]:
        """Zaehlwerte fuer die Abdeckungsanzeige (Konzept 4.13).

        Die Zahl eingelesener Zeilen und die Zahl unterschiedlicher
        Zuordnungen werden ausdruecklich getrennt gefuehrt.
        """
        counts = self.baseline.counts()
        counts["read_link_lines"] = self.read_link_lines
        counts["duplicate_link_lines"] = self.duplicate_link_lines
        return {
            "baseline_id": self.baseline.id,
            "label": self.baseline.label,
            "counts": counts,
            "diagnostics": self.diagnostics.counts(),
            "has_errors": self.diagnostics.has_errors,
        }


def import_project(
    root: Path,
    label: str | None = None,
    layout: ImportLayout | None = None,
    parser: JavaParser | None = None,
    baseline_id: BaselineId | None = None,
) -> ImportReport:
    """Liest einen Projektstand von der Platte."""
    layout = layout or ImportLayout()

    sources: list[tuple[str, str]] = []
    source_dir = root / layout.source_dir
    if source_dir.is_dir():
        for path in sorted(source_dir.rglob("*.java")):
            sources.append((path.relative_to(source_dir).as_posix(), path.read_text(encoding="utf-8")))

    use_cases: list[tuple[str, str]] = []
    use_case_dir = root / layout.use_case_dir
    for pattern in ("*.md", "*.txt"):
        for path in sorted(use_case_dir.glob(pattern)):
            use_cases.append((path.name, path.read_text(encoding="utf-8")))

    link_path = root / layout.trace_link_file
    trace_links = link_path.read_text(encoding="utf-8") if link_path.is_file() else None

    return import_from_texts(
        label=label or root.name,
        use_cases=use_cases,
        sources=sources,
        trace_links=trace_links,
        trace_link_name=layout.trace_link_file,
        parser=parser,
        baseline_id=baseline_id,
    )


def import_from_texts(
    label: str,
    use_cases: list[tuple[str, str]],
    sources: list[tuple[str, str]],
    trace_links: str | None,
    trace_link_name: str = "tracelinks.txt",
    ignored_files: tuple[str, ...] = (),
    parser: JavaParser | None = None,
    baseline_id: BaselineId | None = None,
) -> ImportReport:
    """Baut einen Projektstand aus Dateiinhalten.

    ``use_cases`` und ``sources`` sind Paare aus Name (bei Java-Dateien der
    relative Pfad) und Inhalt. ``trace_links`` ist der Inhalt der Linkdatei, oder
    ``None``, wenn keine mitgeliefert wurde. Der Weg ist derselbe fuer den Import
    von der Platte und fuer den Upload aus der Oberflaeche.
    """
    parser = parser or TreeSitterJavaParser()
    baseline_id = baseline_id or BaselineId(uuid.uuid4().hex[:12])
    diagnostics = Diagnostics()

    for name in ignored_files:
        diagnostics.add(
            DiagnosticCode.IGNORED_FILE,
            Severity.INFO,
            f"Die Datei {name} gehoert nicht zum Import und wurde ignoriert",
            name,
        )

    classes = _classes_from_texts(sources, baseline_id, parser, diagnostics)
    use_case_map = use_cases_from_texts(use_cases, baseline_id, diagnostics)

    if trace_links is not None:
        parsed = parse_trace_links(trace_links, diagnostics, trace_link_name)
        raw_links = parsed.links
        read_lines = parsed.read_lines
        duplicates = parsed.duplicate_lines
    else:
        diagnostics.add(
            DiagnosticCode.MALFORMED_LINE,
            Severity.ERROR,
            f"Trace-Link-Datei {trace_link_name} wurde nicht gefunden",
            trace_link_name,
        )
        raw_links, read_lines, duplicates = (), 0, 0

    resolved = _resolve_links(raw_links, use_case_map, classes, diagnostics, trace_link_name)

    baseline = Baseline.create(
        baseline_id=baseline_id,
        label=label,
        use_cases=use_case_map,
        classes=classes,
        trace_graph=TraceGraph(resolved),
        imported_at=datetime.now(timezone.utc),
    )

    _report_unlinked(baseline, diagnostics)

    return ImportReport(
        baseline=baseline,
        diagnostics=diagnostics,
        read_link_lines=read_lines,
        duplicate_link_lines=duplicates,
    )


def _classes_from_texts(
    sources: list[tuple[str, str]],
    baseline_id: BaselineId,
    parser: JavaParser,
    diagnostics: Diagnostics,
) -> dict[ClassId, JavaClass]:
    """Parst alle Java-Dateien. ``sources`` sind Paare aus relativem Pfad und Inhalt."""
    classes: dict[ClassId, JavaClass] = {}

    for relative, content in sources:
        class_id = class_id_for(relative)

        if class_id in classes:
            # Konzept 4.2: Eine im importierten Stand mehrdeutige Zuordnung
            # wird als Importfehler ausgewiesen.
            diagnostics.add(
                DiagnosticCode.AMBIGUOUS_CLASS,
                Severity.ERROR,
                (
                    f"Der Dateiname {class_id} kommt mehrfach vor: "
                    f"{classes[class_id].relative_path} und {relative}. "
                    "Eine eindeutige Zuordnung ueber den Dateinamen ist nicht moeglich."
                ),
                relative,
            )
            continue

        java_class = parser.parse(baseline_id, class_id, relative, content)
        if not java_class.parsed:
            diagnostics.add(
                DiagnosticCode.PARSE_FAILED,
                Severity.WARNING,
                f"{class_id} konnte nicht vollstaendig verarbeitet werden: "
                f"{java_class.parse_error}",
                relative,
            )
        classes[class_id] = java_class

    return classes


def _resolve_links(
    raw_links: tuple[TraceLink, ...],
    use_cases: dict,
    classes: dict[ClassId, JavaClass],
    diagnostics: Diagnostics,
    source_file: str,
) -> list[TraceLink]:
    """Prueft, ob die referenzierten Kennungen vorhanden sind.

    Eine unaufloesbare Zuordnung wird verworfen und ausgewiesen. Sie wird nicht
    stillschweigend uebergangen, weil der Anwender sonst eine unvollstaendige
    Kandidatenmenge fuer vollstaendig halten koennte.
    """
    resolved: list[TraceLink] = []
    for link in raw_links:
        ok = True
        if link.use_case_id not in use_cases:
            diagnostics.add(
                DiagnosticCode.UNKNOWN_USE_CASE,
                Severity.ERROR,
                f"Zuordnung '{link}' nennt den unbekannten Use Case "
                f"{link.use_case_id}",
                source_file,
            )
            ok = False
        if link.class_id not in classes:
            diagnostics.add(
                DiagnosticCode.UNKNOWN_CLASS,
                Severity.ERROR,
                f"Zuordnung '{link}' nennt die unbekannte Klasse {link.class_id}",
                source_file,
            )
            ok = False
        if ok:
            resolved.append(link)
    return resolved


def _report_unlinked(baseline: Baseline, diagnostics: Diagnostics) -> None:
    """Haelt Artefakte ohne Zuordnung fest.

    Konzept 4.1: Ein nicht verknuepftes Artefakt wird nicht allein deshalb als
    sicher unbeeintraechtigt eingestuft. Der Befund hat deshalb die Stufe
    ``INFO`` und keine Entwarnung zur Folge.
    """
    for class_id in sorted(baseline.unlinked_class_ids):
        diagnostics.add(
            DiagnosticCode.UNLINKED_CLASS,
            Severity.INFO,
            f"Die Klasse {class_id} hat keine deklarierte Zuordnung. "
            "Daraus folgt nicht, dass sie von Aenderungen unberuehrt bleibt.",
        )
    for use_case_id in sorted(baseline.unlinked_use_case_ids):
        diagnostics.add(
            DiagnosticCode.UNLINKED_USE_CASE,
            Severity.WARNING,
            f"Der Use Case {use_case_id} hat keine deklarierte Zuordnung. "
            "Eine Aenderung an ihm liefert keine Kandidatenklassen.",
        )
