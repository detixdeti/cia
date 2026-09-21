"""Teilgraph einer bidirektionalen Auswahl (F2, Konzept 4.1).

Die Property-Tests halten fest, dass die Auswahl die direkte Nachbarschaft
liefert und nicht weiter ausbreitet. Konzept 4.3 schliesst eine unbeschraenkte
Ausbreitung entlang beliebiger Graphpfade und UC-zu-UC-Kanten aus.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from cia.analysis.structural import select_neighbourhood
from cia.domain.ids import ClassId, UseCaseId
from cia.domain.links import TraceGraph, TraceLink
from cia.importing.project import import_project

USE_CASE_NAMES = [f"UC{i}" for i in range(1, 9)]
CLASS_NAMES = [f"K{i}.java" for i in range(1, 9)]

relations = st.sets(
    st.tuples(st.sampled_from(USE_CASE_NAMES), st.sampled_from(CLASS_NAMES)),
    max_size=24,
).map(sorted)

use_case_selections = st.sets(st.sampled_from(USE_CASE_NAMES), max_size=4)
class_selections = st.sets(st.sampled_from(CLASS_NAMES), max_size=4)


def _graph(links) -> TraceGraph:
    return TraceGraph([TraceLink(UseCaseId(u), ClassId(c)) for u, c in links])


@settings(max_examples=200, deadline=None)
@given(links=relations, ucs=use_case_selections, classes=class_selections)
def test_jede_kante_des_teilgraphen_endet_an_einem_ausgewaehlten_knoten(links, ucs, classes):
    hood = select_neighbourhood(
        _graph(links), [UseCaseId(u) for u in ucs], [ClassId(c) for c in classes]
    )

    for link in hood.links:
        assert link.use_case_id in ucs or link.class_id in classes


@settings(max_examples=200, deadline=None)
@given(links=relations, ucs=use_case_selections, classes=class_selections)
def test_jede_kante_eines_ausgewaehlten_knotens_ist_im_teilgraphen(links, ucs, classes):
    graph = _graph(links)
    hood = select_neighbourhood(
        graph, [UseCaseId(u) for u in ucs], [ClassId(c) for c in classes]
    )

    enthalten = {(link.use_case_id, link.class_id) for link in hood.links}
    for link in graph.links:
        if link.use_case_id in ucs or link.class_id in classes:
            assert (link.use_case_id, link.class_id) in enthalten


@settings(max_examples=200, deadline=None)
@given(links=relations, ucs=use_case_selections, classes=class_selections)
def test_teilgraph_enthaelt_ausgewaehlte_knoten_auch_ohne_kante(links, ucs, classes):
    """Ein isolierter Knoten bleibt sichtbar. Seine Isolation ist ein Befund."""
    hood = select_neighbourhood(
        _graph(links), [UseCaseId(u) for u in ucs], [ClassId(c) for c in classes]
    )

    assert {str(u) for u in hood.use_case_ids} >= ucs
    assert {str(c) for c in hood.class_ids} >= classes


@settings(max_examples=200, deadline=None)
@given(links=relations, ucs=use_case_selections)
def test_teilgraph_breitet_nicht_ueber_gemeinsame_klassen_aus(links, ucs):
    """Konzept 4.3: Ein weiterer Use Case an einer gemeinsamen Klasse gelangt
    nicht in den Teilgraphen, solange er nicht selbst ausgewaehlt ist."""
    graph = _graph(links)
    hood = select_neighbourhood(graph, [UseCaseId(u) for u in ucs])

    assert {str(u) for u in hood.use_case_ids} == ucs


def test_teilgraph_verdoppelt_keine_kante_bei_beidseitiger_auswahl():
    graph = _graph([("UC1", "K1.java")])
    hood = select_neighbourhood(graph, [UseCaseId("UC1")], [ClassId("K1.java")])

    assert len(hood.links) == 1


def test_teilgraph_am_beispielprojekt_zeigt_nur_direkte_nachbarn(fixture_root):
    baseline = import_project(fixture_root).baseline
    hood = select_neighbourhood(baseline.trace_graph, [UseCaseId("UC3")])

    assert hood.use_case_ids == {UseCaseId("UC3")}
    assert hood.class_ids == {ClassId("Mitglied.java")}

