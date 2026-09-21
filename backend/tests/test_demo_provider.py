"""Demo-Anbieter fuer Vorfuehrungen.

Er liefert Beispielantworten, damit die Oberflaeche Vorschlaege zeigen kann. Die
Tests stellen sicher, dass seine Antworten von der normalen Pruefung akzeptiert
werden und dass sie nie wie eine echte Bewertung aussehen.
"""

from __future__ import annotations

import json

from cia.domain.ids import ClassId, UseCaseId
from cia.domain.scenario import (
    ChangeKind,
    CodeChange,
    Direction,
    RequirementChange,
    Scenario,
)
from cia.importing.project import import_project
from cia.llm.answer import AnswerState, Status
from cia.llm.backward import DeviationStatus, run_backward_analysis
from cia.llm.demo import DemoProvider
from cia.llm.run import run_forward_analysis
from conftest import scenario_id


def _vorwaerts(fixture_root):
    baseline = import_project(fixture_root).baseline
    szenario = Scenario(
        id=scenario_id(),
        baseline_id=baseline.id,
        title="t",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=(RequirementChange(ChangeKind.DEACTIVATE, UseCaseId("UC5")),),
    )
    return baseline, run_forward_analysis(baseline, szenario, DemoProvider())


def test_demo_hat_keine_einstellungen_und_heisst_demo():
    anbieter = DemoProvider()

    assert anbieter.name == "demo"
    assert anbieter.settings == {}


def test_demo_antworten_der_anforderungsrichtung_bestehen_die_pruefung(fixture_root):
    baseline, lauf = _vorwaerts(fixture_root)

    for ergebnis in lauf.results:
        antwort = ergebnis.analysis.answer
        assert antwort.state is AnswerState.ANSWERED
        assert all(e.problems == () for e in antwort.entries)


def test_demo_zeigt_alle_drei_zustaende_und_laesst_den_rest_offen(fixture_root):
    baseline, lauf = _vorwaerts(fixture_root)
    katalog = next(r for r in lauf.results if r.class_id == "Katalog.java").analysis.answer

    zustaende = [e.entry.status for e in katalog.entries]

    assert zustaende == [Status.CHANGE_PROPOSED, Status.NO_CHANGE_VISIBLE, Status.NOT_ASSESSABLE]
    methoden = len(baseline.classes[ClassId("Katalog.java")].methods)
    assert len(katalog.unanswered_methods) == methoden - 3


def test_jeder_freitext_der_demo_ist_als_demo_gekennzeichnet(fixture_root):
    baseline, lauf = _vorwaerts(fixture_root)

    for ergebnis in lauf.results:
        antwort = ergebnis.analysis.answer
        for eintrag in antwort.entries:
            for text in (eintrag.entry.reason, eintrag.entry.proposal, eintrag.entry.use_case_passage):
                assert not text or text.startswith("[DEMO]")
        for text in (*antwort.assumptions, *antwort.missing_context):
            assert text.startswith("[DEMO]")


def test_klasse_mit_einer_methode_bekommt_nur_einen_eintrag():
    prompt = "Regeln\n\nKLASSE: K.java\n\nMETHODEN\n\n### a()\nvoid a() {}"

    antwort = json.loads(DemoProvider().complete(prompt))

    assert [e["target"] for e in antwort["entries"]] == ["a()"]


def test_klasse_ohne_methoden_bekommt_keine_eintraege():
    antwort = json.loads(DemoProvider().complete("Regeln\n\nKLASSE: K.java\n\nMETHODEN"))

    assert antwort["entries"] == []


def test_demo_antworten_der_gegenrichtung_bestehen_die_pruefung_und_sind_verschieden(fixture_root):
    baseline = import_project(fixture_root).baseline
    szenario = Scenario(
        id=scenario_id(),
        baseline_id=baseline.id,
        title="t",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=(
            CodeChange(ClassId("Ausleihe.java"), "alt", "neu"),
        ),
    )

    lauf = run_backward_analysis(baseline, szenario, DemoProvider())

    zustaende = {r.use_case_id: r.answer.assessment.status for r in lauf.results}
    assert all(r.answer.state is AnswerState.ANSWERED for r in lauf.results)
    assert zustaende["UC1"] is DeviationStatus.POSSIBLE_DEVIATION
    assert zustaende["UC2"] is DeviationStatus.NO_DEVIATION_VISIBLE
    assert len(set(zustaende.values())) >= 2


def test_demo_abweichung_der_gegenrichtung_ist_gekennzeichnet_und_hat_einen_textvorschlag(
    fixture_root,
):
    baseline = import_project(fixture_root).baseline
    szenario = Scenario(
        id=scenario_id(),
        baseline_id=baseline.id,
        title="t",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=(CodeChange(ClassId("Ausleihe.java"), "alt", "neu"),),
    )

    lauf = run_backward_analysis(baseline, szenario, DemoProvider())
    uc1 = next(r for r in lauf.results if r.use_case_id == "UC1").answer.assessment

    assert uc1.reason.startswith("[DEMO]")
    assert uc1.proposed_text.startswith("[DEMO]")
