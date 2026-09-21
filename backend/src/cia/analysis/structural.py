"""Strukturelle Auswahl der Pruefkandidaten.

Umsetzung von Konzept Abschnitt 4.3 bis 4.5. Dieses Modul haengt ausdruecklich
von keiner Modellanbindung ab. Seine Ergebnisse folgen allein aus der
deklarierten Relation T und sind damit reproduzierbar. Die inhaltliche
Beurteilung geschieht erst in einem nachgelagerten Schritt und darf die
Herkunft dieser Kandidaten weder ersetzen noch verdecken.

Eine unbeschraenkte Ausbreitung entlang beliebiger Graphpfade findet nicht
statt. Andernfalls koennten gemeinsam genutzte Klassen grosse Teile des Graphen
markieren, ohne dass fuer jede Weitergabe ein inhaltlicher Grund vorliegt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..domain.baseline import Baseline
from ..domain.ids import ClassId, UseCaseId
from ..domain.links import TraceGraph, TraceLink
from ..domain.scenario import ChangeKind, Direction, Scenario


@dataclass(frozen=True, slots=True)
class ClassCandidate:
    """Eine zu pruefende Klasse mit ihrer Herkunft.

    ``triggering_use_case_ids`` benennt die geaenderten Use Cases, ueber die
    diese Klasse in die Menge gelangt ist. ``preservation_context_ids`` enthaelt
    die weiteren aktiven Use Cases derselben Klasse. Konzept 4.3 legt fest, dass
    diese ausschliesslich als Erhaltungskontext erscheinen und in der
    Anforderungsrichtung nie als betroffen markiert werden.
    """

    class_id: ClassId
    triggering_use_case_ids: frozenset[UseCaseId]
    preservation_context_ids: frozenset[UseCaseId]
    parsed: bool = True

    @property
    def has_remaining_use_cases(self) -> bool:
        """Ob der Klasse nach der Aenderung noch ein aktiver Use Case bleibt.

        Konzept 4.5 ist hier eindeutig: Auch wenn keiner bleibt, folgt daraus
        keine Loeschfreigabe. Die Eigenschaft ist eine Anzeige, kein Kriterium.
        """
        return bool(self.preservation_context_ids)


@dataclass(frozen=True, slots=True)
class UnresolvedChange:
    """Eine Aenderung, fuer die keine Zuordnung bestimmt werden konnte."""

    use_case_id: UseCaseId
    reason: str


@dataclass(frozen=True, slots=True)
class ForwardSelection:
    """Ergebnis der Auswahl in der Anforderungsrichtung."""

    changed_use_case_ids: frozenset[UseCaseId]
    candidates: tuple[ClassCandidate, ...]
    unresolved: tuple[UnresolvedChange, ...] = ()

    @property
    def candidate_class_ids(self) -> frozenset[ClassId]:
        return frozenset(c.class_id for c in self.candidates)

    @property
    def unparsed_candidate_ids(self) -> frozenset[ClassId]:
        """Kandidaten, die der Parser nicht verarbeiten konnte (Konzept 4.13)."""
        return frozenset(c.class_id for c in self.candidates if not c.parsed)


@dataclass(frozen=True, slots=True)
class UseCaseCandidate:
    """Ein in der Gegenrichtung zu pruefender Use Case."""

    use_case_id: UseCaseId
    triggering_class_ids: frozenset[ClassId]


@dataclass(frozen=True, slots=True)
class BackwardSelection:
    """Ergebnis der Auswahl in der Gegenrichtung (Konzept 4.6)."""

    changed_class_ids: frozenset[ClassId]
    candidates: tuple[UseCaseCandidate, ...]
    #: Geaenderte Klassen ohne deklarierte Zuordnung. Sie werden als nicht
    #: zuordenbar ausgewiesen, nicht als unbeeintraechtigt.
    unassignable_class_ids: frozenset[ClassId] = frozenset()

    @property
    def candidate_use_case_ids(self) -> frozenset[UseCaseId]:
        return frozenset(c.use_case_id for c in self.candidates)


@dataclass(frozen=True, slots=True)
class Neighbourhood:
    """Teilgraph zu einer bidirektionalen Auswahl (F2, Konzept 4.1).

    Enthalten sind die ausgewaehlten Knoten, ihre direkten Nachbarn und die
    Kanten, die an einem ausgewaehlten Knoten enden. Weiter wird nicht
    ausgebreitet: Zwei Use Cases, die dieselbe Klasse nutzen, sind im Teilgraphen
    nicht verbunden, und es entsteht keine UC-zu-UC-Kante (Konzept 4.3).
    """

    selected_use_case_ids: frozenset[UseCaseId]
    selected_class_ids: frozenset[ClassId]
    use_case_ids: frozenset[UseCaseId]
    class_ids: frozenset[ClassId]
    links: tuple[TraceLink, ...]


def select_neighbourhood(
    graph: TraceGraph,
    use_case_ids: Iterable[UseCaseId] = (),
    class_ids: Iterable[ClassId] = (),
) -> Neighbourhood:
    """Bestimmt den Teilgraphen zu ausgewaehlten Use Cases und Klassen.

    Ein ausgewaehlter Use Case macht seine Klassen zugaenglich, eine
    ausgewaehlte Klasse ihre Use Cases (Konzept 4.1). Ein ausgewaehlter Knoten
    ohne Kante bleibt im Ergebnis erhalten; seine Isolation ist ein Befund und
    keine Entwarnung (Konzept 4.13).
    """
    selected_ucs = frozenset(use_case_ids)
    selected_classes = frozenset(class_ids)

    links = tuple(
        sorted(
            (
                link
                for link in graph.links
                if link.use_case_id in selected_ucs or link.class_id in selected_classes
            ),
            key=lambda link: (link.use_case_id, link.class_id),
        )
    )
    return Neighbourhood(
        selected_use_case_ids=selected_ucs,
        selected_class_ids=selected_classes,
        use_case_ids=selected_ucs | frozenset(link.use_case_id for link in links),
        class_ids=selected_classes | frozenset(link.class_id for link in links),
        links=links,
    )


def effective_graph(baseline: Baseline, scenario: Scenario) -> TraceGraph:
    """Die fuer ein Szenario gueltige Relation.

    Sie besteht aus den importierten Kanten und den manuellen Zuordnungen eines
    neu angelegten Use Cases (Konzept 4.3). Die Baseline bleibt unveraendert.
    """
    extra = scenario.scenario_links
    if not extra:
        return baseline.trace_graph
    return baseline.trace_graph.extended_with(extra)


def active_use_case_ids(baseline: Baseline, scenario: Scenario) -> frozenset[UseCaseId]:
    """Die im Szenario weiterhin aktiven Use Cases.

    Ein deaktivierter Use Case bleibt fuer die Analyse verfuegbar, gilt aber als
    kuenftig inaktiv (Konzept 4.3). Ein neu angelegter Use Case ist aktiv.
    """
    active = {uid for uid, uc in baseline.use_cases.items() if uc.active}
    for change in scenario.requirement_changes:
        if change.kind is ChangeKind.DEACTIVATE:
            active.discard(change.use_case_id)
        elif change.kind is ChangeKind.ADD:
            active.add(change.use_case_id)
    return frozenset(active)


def select_forward(baseline: Baseline, scenario: Scenario) -> ForwardSelection:
    """Bestimmt die Kandidatenklassen einer Anforderungsaenderung.

    Fuer einen geaenderten Use Case ``u`` ergibt sich ``C0(u) = {c | (u, c) in
    T}``. Bei mehreren geaenderten Use Cases wird die Vereinigung ihrer
    Nachbarschaften gebildet (Konzept 4.3).
    """
    if scenario.direction is not Direction.REQUIREMENT_TO_CODE:
        raise ValueError("select_forward erwartet die Anforderungsrichtung")

    graph = effective_graph(baseline, scenario)
    changed = scenario.changed_use_case_ids
    active = active_use_case_ids(baseline, scenario)

    triggers: dict[ClassId, set[UseCaseId]] = {}
    unresolved: list[UnresolvedChange] = []

    for change in scenario.requirement_changes:
        classes = graph.classes_of(change.use_case_id)
        if not classes:
            # Konzept 4.3: Ohne manuelle Auswahl wird keine Zuordnung erzeugt.
            # Die leere Kandidatenmenge bedeutet nicht, dass die Aenderung
            # wirkungslos waere.
            reason = (
                "keine Zuordnung fuer die Analyse vorhanden"
                if change.kind is ChangeKind.ADD
                else "keine deklarierte Zuordnung im Ausgangsstand"
            )
            unresolved.append(UnresolvedChange(change.use_case_id, reason))
            continue
        for class_id in classes:
            triggers.setdefault(class_id, set()).add(change.use_case_id)

    candidates: list[ClassCandidate] = []
    for class_id in sorted(triggers):
        # Erhaltungskontext: weitere aktive Use Cases derselben Klasse, die
        # nicht selbst Gegenstand des Auftrags sind.
        context = frozenset(
            uid for uid in graph.use_cases_of(class_id) if uid in active and uid not in changed
        )
        java_class = baseline.java_class(class_id)
        candidates.append(
            ClassCandidate(
                class_id=class_id,
                triggering_use_case_ids=frozenset(triggers[class_id]),
                preservation_context_ids=context,
                parsed=java_class.parsed if java_class is not None else False,
            )
        )

    return ForwardSelection(
        changed_use_case_ids=changed,
        candidates=tuple(candidates),
        unresolved=tuple(unresolved),
    )


def select_backward(baseline: Baseline, scenario: Scenario) -> BackwardSelection:
    """Bestimmt die Kandidaten-Use-Cases einer Codeaenderung.

    Aus der Menge geaenderter Klassen ``C_delta`` wird ``U0(C_delta) = {u |
    es gibt c in C_delta mit (u, c) in T}`` bestimmt (Konzept 4.6). Mehrfach
    gefundene Use Cases werden zusammengefuehrt, ihre ausloesenden Klassen
    bleiben jedoch gemeinsam als Kontext erhalten. Konzept 4.4 begruendet das:
    Zwei einzeln plausibel erscheinende Aenderungen koennen erst in ihrer
    Kombination eine Erfolgsbedingung verletzen.
    """
    if scenario.direction is not Direction.CODE_TO_REQUIREMENT:
        raise ValueError("select_backward erwartet die Gegenrichtung")

    graph = effective_graph(baseline, scenario)
    changed = scenario.changed_class_ids

    triggers: dict[UseCaseId, set[ClassId]] = {}
    unassignable: set[ClassId] = set()

    for class_id in changed:
        use_cases = graph.use_cases_of(class_id)
        if not use_cases:
            unassignable.add(class_id)
            continue
        for use_case_id in use_cases:
            triggers.setdefault(use_case_id, set()).add(class_id)

    candidates = tuple(
        UseCaseCandidate(use_case_id=uid, triggering_class_ids=frozenset(triggers[uid]))
        for uid in sorted(triggers)
    )

    return BackwardSelection(
        changed_class_ids=changed,
        candidates=candidates,
        unassignable_class_ids=frozenset(unassignable),
    )
