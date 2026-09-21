"""Property-Tests der strukturellen Auswahl.

Konzept Abschnitt 4.4 nennt vier ueberpruefbare Eigenschaften der
Kandidatenberechnung. Sie folgen aus der Mengendefinition und betreffen
ausschliesslich die strukturelle Auswahl, nicht die nachfolgende inhaltliche
Bewertung. Die folgenden Tests pruefen sie ueber zufaellig erzeugte Relationen.

Damit steht in der Ausarbeitung nicht die Behauptung, die Auswahl funktioniere,
sondern ein nachgewiesener Befund ueber eine definierte Eigenschaft.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from cia.analysis.structural import select_backward, select_forward
from cia.domain.ids import ClassId, UseCaseId
from cia.domain.scenario import (
    ChangeKind,
    CodeChange,
    Direction,
    RequirementChange,
    Scenario,
)
from conftest import TEST_BASELINE, make_baseline, scenario_id

USE_CASE_NAMES = [f"UC{i}" for i in range(1, 9)]
CLASS_NAMES = [f"K{i}.java" for i in range(1, 9)]

#: Eine zufaellige Relation T als Menge von Kantenpaaren.
relations = st.sets(
    st.tuples(st.sampled_from(USE_CASE_NAMES), st.sampled_from(CLASS_NAMES)),
    min_size=0,
    max_size=24,
).map(sorted)


def forward_scenario(changed: list[str]) -> Scenario:
    return Scenario(
        id=scenario_id(),
        baseline_id=TEST_BASELINE,
        title="t",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=tuple(
            RequirementChange(ChangeKind.DEACTIVATE, UseCaseId(u)) for u in changed
        ),
    )


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    changed=st.lists(st.sampled_from(USE_CASE_NAMES), min_size=1, max_size=4, unique=True),
)
def test_jeder_kandidat_hat_einen_link_zu_einer_geaenderten_anforderung(links, changed):
    """Eigenschaft 1 (Konzept 4.4).

    Jede ausgegebene Kandidatenklasse muss mindestens einen Link zu einem
    geaenderten Use Case besitzen.
    """
    baseline = make_baseline(links, extra_use_cases=changed)
    selection = select_forward(baseline, forward_scenario(changed))
    graph = baseline.trace_graph

    for candidate in selection.candidates:
        auslöser = [
            u for u in changed if graph.contains(UseCaseId(u), candidate.class_id)
        ]
        assert auslöser, (
            f"{candidate.class_id} wurde ausgegeben, hat aber keinen Link zu einem "
            f"geaenderten Use Case"
        )
        assert candidate.triggering_use_case_ids == frozenset(
            UseCaseId(u) for u in auslöser
        )


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    changed=st.lists(st.sampled_from(USE_CASE_NAMES), min_size=1, max_size=4, unique=True),
)
def test_jede_verlinkte_klasse_ist_kandidat(links, changed):
    """Eigenschaft 2 (Konzept 4.4).

    Umgekehrt muss jede ueber einen solchen Link zugeordnete Klasse in der
    Kandidatenmenge vorkommen. Zusammen mit Eigenschaft 1 ist die Auswahl damit
    genau die Vereinigung der Nachbarschaften.
    """
    baseline = make_baseline(links, extra_use_cases=changed)
    selection = select_forward(baseline, forward_scenario(changed))

    erwartet = set()
    for use_case in changed:
        erwartet |= set(baseline.trace_graph.classes_of(UseCaseId(use_case)))

    assert selection.candidate_class_ids == frozenset(erwartet)


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    changed=st.lists(st.sampled_from(USE_CASE_NAMES), min_size=1, max_size=4, unique=True),
    wiederholungen=st.integers(min_value=1, max_value=3),
)
def test_mehrfache_links_aendern_die_menge_nicht(links, changed, wiederholungen):
    """Eigenschaft 3 (Konzept 4.4).

    Mehrfach vorkommende Links aendern die Menge nicht. Konzept 4.2 haelt
    zusaetzlich fest, dass daraus keine zusaetzliche Evidenz folgt.
    """
    einfach = make_baseline(links, extra_use_cases=changed)
    mehrfach = make_baseline(list(links) * wiederholungen, extra_use_cases=changed)

    szenario = forward_scenario(changed)
    assert (
        select_forward(einfach, szenario).candidate_class_ids
        == select_forward(mehrfach, szenario).candidate_class_ids
    )


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    changed=st.lists(st.sampled_from(USE_CASE_NAMES), min_size=1, max_size=3, unique=True),
    zusatz=st.sampled_from(USE_CASE_NAMES),
)
def test_zusaetzliche_anforderung_verkleinert_die_menge_nicht(links, changed, zusatz):
    """Eigenschaft 4 (Konzept 4.4).

    Wird bei unveraendertem Projektstand ein weiterer Use Case zum
    Aenderungsauftrag hinzugefuegt, kann die Vereinigung der Kandidatenmengen
    nicht kleiner werden.

    Konzept 4.4 grenzt ausdruecklich ab, dass diese Monotonie nicht fuer die
    inhaltliche Bewertung gilt: Ein zusaetzlicher Auftrag kann einen zunaechst
    erwarteten Anpassungsbedarf aufheben.
    """
    erweitert = list(dict.fromkeys([*changed, zusatz]))
    baseline = make_baseline(links, extra_use_cases=erweitert)

    klein = select_forward(baseline, forward_scenario(changed)).candidate_class_ids
    gross = select_forward(baseline, forward_scenario(erweitert)).candidate_class_ids

    assert klein <= gross


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    geaendert=st.lists(st.sampled_from(CLASS_NAMES), min_size=1, max_size=4, unique=True),
)
def test_gegenrichtung_liefert_die_inverse_nachbarschaft(links, geaendert):
    """Die Gegenrichtung nutzt dieselbe Relation invers (Konzept 4.6).

    Ein mehrfach gefundener Use Case erscheint genau einmal, seine ausloesenden
    Klassen bleiben aber gemeinsam als Kontext erhalten.
    """
    baseline = make_baseline(links, extra_classes=geaendert)
    szenario = Scenario(
        id=scenario_id(),
        baseline_id=TEST_BASELINE,
        title="t",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=tuple(
            CodeChange(ClassId(c), before="alt", after="neu") for c in geaendert
        ),
    )
    selection = select_backward(baseline, szenario)

    erwartet = set()
    for class_id in geaendert:
        erwartet |= set(baseline.trace_graph.use_cases_of(ClassId(class_id)))

    assert selection.candidate_use_case_ids == frozenset(erwartet)
    assert len({c.use_case_id for c in selection.candidates}) == len(selection.candidates)

    for candidate in selection.candidates:
        for class_id in candidate.triggering_class_ids:
            assert baseline.trace_graph.contains(candidate.use_case_id, class_id)


@settings(max_examples=200, deadline=None)
@given(
    links=relations,
    geaendert=st.lists(st.sampled_from(CLASS_NAMES), min_size=1, max_size=4, unique=True),
)
def test_klassen_ohne_zuordnung_gelten_als_nicht_zuordenbar(links, geaendert):
    """Konzept 4.6: Hinzugefuegte Klassen ohne deklarierte Zuordnung werden als
    nicht zuordenbar ausgewiesen. Sie gelten ausdruecklich nicht als
    unbeeintraechtigt."""
    baseline = make_baseline(links, extra_classes=geaendert)
    szenario = Scenario(
        id=scenario_id(),
        baseline_id=TEST_BASELINE,
        title="t",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=tuple(
            CodeChange(ClassId(c), before="alt", after="neu") for c in geaendert
        ),
    )
    selection = select_backward(baseline, szenario)

    for class_id in selection.unassignable_class_ids:
        assert not baseline.trace_graph.use_cases_of(class_id)

    abgedeckt = selection.unassignable_class_ids | {
        cid for c in selection.candidates for cid in c.triggering_class_ids
    }
    assert abgedeckt == frozenset(ClassId(c) for c in geaendert)
