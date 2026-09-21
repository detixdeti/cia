"""Die Trace-Link-Relation T zwischen Use Cases und Klassen.

Umsetzung von Konzept Abschnitt 4.3. Die Relation ist die einzige Quelle der
strukturellen Kandidatenbestimmung. Sie enthaelt ausschliesslich Kanten der
Form Use Case zu Klasse. UC-zu-UC-Kanten sind ausgeschlossen und werden weder
importiert noch aus gemeinsam genutzten Klassen abgeleitet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from .ids import ClassId, UseCaseId


class LinkOrigin(str, Enum):
    """Herkunft einer Kante.

    Konzept 4.3 trennt importierte Zuordnungen von denen, die der Anwender fuer
    einen neu angelegten Use Case innerhalb eines Szenarios festlegt. Das
    Werkzeug muss beide auseinanderhalten koennen, damit eine Szenariozuordnung
    nicht als Befund des Ausgangsstands erscheint.
    """

    #: Aus der Trace-Link-Datei des Projektstands uebernommen.
    IMPORTED = "imported"
    #: Vom Anwender im Szenario festgelegt (Konzept 4.3, neuer Use Case).
    SCENARIO = "scenario"


@dataclass(frozen=True, slots=True)
class TraceLink:
    """Eine einzelne Zuordnung ``(u, c) in T``."""

    use_case_id: UseCaseId
    class_id: ClassId
    origin: LinkOrigin = LinkOrigin.IMPORTED

    def __str__(self) -> str:
        return f"{self.use_case_id} -> {self.class_id}"


@dataclass(frozen=True, slots=True)
class SourceLine:
    """Eine Zeile der Linkdatei mit ihrer Herkunft.

    Konzept 4.13 verlangt, die Zahl eingelesener Zeilen von der Zahl
    unterschiedlicher Zuordnungen zu unterscheiden. Dafuer bleibt die
    Zeilenherkunft jeder Kante erhalten.
    """

    line_number: int
    raw: str


class TraceGraph:
    """Unveraenderliche Sicht auf die Relation T.

    Die Nachbarschaften werden beim Aufbau einmal berechnet. Mehrfach
    deklarierte identische Zuordnungen werden dabei zu einer Kante
    zusammengefasst; Konzept 4.2 haelt fest, dass daraus keine zusaetzliche
    Evidenz abgeleitet wird.
    """

    __slots__ = ("_links", "_by_use_case", "_by_class")

    def __init__(self, links: Iterable[TraceLink]) -> None:
        unique: dict[tuple[UseCaseId, ClassId], TraceLink] = {}
        for link in links:
            key = (link.use_case_id, link.class_id)
            existing = unique.get(key)
            if existing is None:
                unique[key] = link
            elif existing.origin != link.origin:
                # Eine im Ausgangsstand deklarierte Zuordnung bleibt
                # importiert, auch wenn sie im Szenario erneut ausgewaehlt
                # wird. Sonst erschiene eine vorhandene Kante als
                # Anwendereingabe.
                unique[key] = TraceLink(
                    link.use_case_id, link.class_id, LinkOrigin.IMPORTED
                )

        self._links: tuple[TraceLink, ...] = tuple(unique.values())

        by_uc: dict[UseCaseId, set[ClassId]] = {}
        by_cls: dict[ClassId, set[UseCaseId]] = {}
        for link in self._links:
            by_uc.setdefault(link.use_case_id, set()).add(link.class_id)
            by_cls.setdefault(link.class_id, set()).add(link.use_case_id)

        self._by_use_case: Mapping[UseCaseId, frozenset[ClassId]] = {
            k: frozenset(v) for k, v in by_uc.items()
        }
        self._by_class: Mapping[ClassId, frozenset[UseCaseId]] = {
            k: frozenset(v) for k, v in by_cls.items()
        }

    @property
    def links(self) -> tuple[TraceLink, ...]:
        """Die eindeutigen Kanten der Relation."""
        return self._links

    def classes_of(self, use_case_id: UseCaseId) -> frozenset[ClassId]:
        """Die Nachbarschaft eines Use Cases: ``{c | (u, c) in T}``."""
        return self._by_use_case.get(use_case_id, frozenset())

    def use_cases_of(self, class_id: ClassId) -> frozenset[UseCaseId]:
        """Die inverse Nachbarschaft einer Klasse: ``{u | (u, c) in T}``."""
        return self._by_class.get(class_id, frozenset())

    def contains(self, use_case_id: UseCaseId, class_id: ClassId) -> bool:
        return class_id in self.classes_of(use_case_id)

    def linked_use_case_ids(self) -> frozenset[UseCaseId]:
        return frozenset(self._by_use_case)

    def linked_class_ids(self) -> frozenset[ClassId]:
        return frozenset(self._by_class)

    def extended_with(self, extra: Iterable[TraceLink]) -> TraceGraph:
        """Neuer Graph mit zusaetzlichen Kanten.

        Wird fuer die manuellen Szenariozuordnungen eines neu angelegten Use
        Cases verwendet (Konzept 4.3). Der Ausgangsgraph bleibt unveraendert.
        """
        return TraceGraph([*self._links, *extra])

    def __len__(self) -> int:
        return len(self._links)

    def __repr__(self) -> str:
        return (
            f"TraceGraph(links={len(self._links)}, "
            f"use_cases={len(self._by_use_case)}, classes={len(self._by_class)})"
        )
