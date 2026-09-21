"""Abbildung von Baseline und Teilgraph auf die Graphdarstellung (F2).

Alle importierten Artefakte erscheinen als Knoten, auch solche ohne Zuordnung.
Der Graph zeigt ausschliesslich Kanten der Relation T. Layoutkoordinaten liefert
die Schnittstelle nicht; raeumliche Naehe soll kein Abhaengigkeitsnachweis sein
(Konzept 4.8).
"""

from __future__ import annotations

from ..analysis.structural import Neighbourhood
from ..domain.baseline import Baseline
from ..domain.ids import ClassId, UseCaseId
from ..domain.links import TraceLink
from .schemas import GraphEdgeOut, GraphNodeOut, GraphOut


def use_case_node_id(use_case_id: str) -> str:
    return f"uc:{use_case_id}"


def class_node_id(class_id: str) -> str:
    return f"class:{class_id}"


def _use_case_node(
    baseline: Baseline, use_case_id: UseCaseId, selected: bool | None
) -> GraphNodeOut:
    use_case = baseline.use_cases[use_case_id]
    return GraphNodeOut(
        id=use_case_node_id(use_case_id),
        kind="use_case",
        ref=use_case_id,
        label=f"{use_case_id}: {use_case.title}",
        linked=use_case_id in baseline.trace_graph.linked_use_case_ids(),
        selected=selected,
        active=use_case.active,
    )


def _class_node(baseline: Baseline, class_id: ClassId, selected: bool | None) -> GraphNodeOut:
    java_class = baseline.classes[class_id]
    return GraphNodeOut(
        id=class_node_id(class_id),
        kind="class",
        ref=class_id,
        label=java_class.file_name,
        linked=class_id in baseline.trace_graph.linked_class_ids(),
        selected=selected,
        parsed=java_class.parsed,
        method_count=len(java_class.methods),
    )


def _edge(link: TraceLink) -> GraphEdgeOut:
    return GraphEdgeOut(
        id=f"{link.use_case_id}->{link.class_id}",
        source=use_case_node_id(link.use_case_id),
        target=class_node_id(link.class_id),
        origin=link.origin.value,
    )


def build_graph(baseline: Baseline) -> GraphOut:
    """Der vollstaendige importierte Graph."""
    nodes = [_use_case_node(baseline, uid, None) for uid in sorted(baseline.use_cases)]
    nodes += [_class_node(baseline, cid, None) for cid in sorted(baseline.classes)]
    return GraphOut(
        baseline_id=baseline.id,
        nodes=nodes,
        edges=[_edge(link) for link in baseline.trace_graph.links],
    )


def build_subgraph(baseline: Baseline, hood: Neighbourhood) -> GraphOut:
    """Der Teilgraph einer bidirektionalen Auswahl."""
    nodes = [
        _use_case_node(baseline, uid, uid in hood.selected_use_case_ids)
        for uid in sorted(hood.use_case_ids)
    ]
    nodes += [
        _class_node(baseline, cid, cid in hood.selected_class_ids)
        for cid in sorted(hood.class_ids)
    ]
    return GraphOut(
        baseline_id=baseline.id,
        nodes=nodes,
        edges=[_edge(link) for link in hood.links],
    )
