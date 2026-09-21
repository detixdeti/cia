"""Der importierte Projektstand.

Umsetzung von Konzept Abschnitt 4.2: Anforderungen, Java-Dateien und Linkdatei
werden einem gemeinsamen Ausgangsstand zugeordnet. Die Linkdatei liefert dafuer
keine eigene Versionsinformation. Eine Baseline wird nach dem Import nicht mehr
veraendert; jedes Szenario arbeitet auf einer Kopie.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from .artifacts import JavaClass, UseCase
from .ids import BaselineId, ClassId, UseCaseId
from .links import TraceGraph


@dataclass(frozen=True, slots=True)
class Baseline:
    """Ein unveraenderlicher Projektstand."""

    id: BaselineId
    label: str
    use_cases: Mapping[UseCaseId, UseCase]
    classes: Mapping[ClassId, JavaClass]
    trace_graph: TraceGraph
    imported_at: datetime

    @staticmethod
    def create(
        baseline_id: BaselineId,
        label: str,
        use_cases: Mapping[UseCaseId, UseCase],
        classes: Mapping[ClassId, JavaClass],
        trace_graph: TraceGraph,
        imported_at: datetime | None = None,
    ) -> Baseline:
        return Baseline(
            id=baseline_id,
            label=label,
            use_cases=dict(use_cases),
            classes=dict(classes),
            trace_graph=trace_graph,
            imported_at=imported_at or datetime.now(timezone.utc),
        )

    def use_case(self, use_case_id: UseCaseId) -> UseCase | None:
        return self.use_cases.get(use_case_id)

    def java_class(self, class_id: ClassId) -> JavaClass | None:
        return self.classes.get(class_id)

    @property
    def unparsed_classes(self) -> tuple[JavaClass, ...]:
        """Klassen, die der Parser nicht verarbeiten konnte.

        Konzept 4.13 verlangt, dass diese unabhaengig vom Ergebnis der uebrigen
        Klassen sichtbar bleiben.
        """
        return tuple(c for c in self.classes.values() if not c.parsed)

    @property
    def unlinked_class_ids(self) -> frozenset[ClassId]:
        """Importierte Klassen ohne jede deklarierte Zuordnung.

        Konzept 4.1: Ein nicht verknuepftes Artefakt gilt nicht allein deshalb
        als sicher unbeeintraechtigt. Die Menge dient der Abdeckungsanzeige,
        nicht einer Entwarnung.
        """
        return frozenset(self.classes) - self.trace_graph.linked_class_ids()

    @property
    def unlinked_use_case_ids(self) -> frozenset[UseCaseId]:
        return frozenset(self.use_cases) - self.trace_graph.linked_use_case_ids()

    def counts(self) -> dict[str, int]:
        """Zaehlwerte fuer die Abdeckungsanzeige (Konzept 4.13)."""
        return {
            "use_cases": len(self.use_cases),
            "classes": len(self.classes),
            "parsed_classes": sum(1 for c in self.classes.values() if c.parsed),
            "methods": sum(len(c.methods) for c in self.classes.values()),
            "trace_links": len(self.trace_graph),
            "unlinked_classes": len(self.unlinked_class_ids),
            "unlinked_use_cases": len(self.unlinked_use_case_ids),
        }
