"""Gegenrichtung: Codeaenderung gegen Use Cases pruefen (F6, Konzept 4.7).

Wie bei der Anforderungsrichtung laufen alle Tests ohne echtes Modell. Geprueft
wird die technische Seite: Was geht ins Paket, was passiert mit einer Antwort,
und dass nichts zur Entwarnung wird.
"""

from __future__ import annotations

import json

import pytest

from cia.analysis.structural import select_backward
from cia.domain.artifacts import MethodSignature
from cia.domain.baseline import Baseline
from cia.domain.ids import ClassId, UseCaseId
from cia.domain.scenario import CodeChange, Direction, Scenario
from cia.importing.project import import_project
from cia.llm.answer import AnswerState
from cia.llm.backward import (
    AssessmentProblem,
    DeviationStatus,
    analyze_use_case,
    build_use_case_package,
    check_assessment,
    render_use_case_prompt,
    run_backward_analysis,
)
from cia.llm.mock import MockProvider
from cia.llm.provider import LlmError
from conftest import scenario_id

SUCHE = MethodSignature("suche", ("String",))


@pytest.fixture(scope="module")
def baseline(fixture_root) -> Baseline:
    return import_project(fixture_root).baseline


def _aenderung(baseline: Baseline, class_id: str, signature: MethodSignature | None = None):
    java_class = baseline.classes[ClassId(class_id)]
    vorher = java_class.source if signature is None else java_class.method(signature).source
    return CodeChange(ClassId(class_id), vorher, "// geaendert", signature)


def _szenario(baseline: Baseline, *aenderungen: CodeChange) -> Scenario:
    return Scenario(
        id=scenario_id(),
        baseline_id=baseline.id,
        title="t",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=tuple(aenderungen),
    )


def _paket(baseline: Baseline, szenario: Scenario, use_case_id: str):
    auswahl = select_backward(baseline, szenario)
    kandidat = next(c for c in auswahl.candidates if c.use_case_id == use_case_id)
    return build_use_case_package(baseline, szenario, kandidat)


def _antwort(**felder) -> str:
    antwort = {
        "status": "no_deviation_visible",
        "affected_passage": "",
        "reason": "",
        "proposed_text": None,
    }
    antwort.update(felder)
    return json.dumps(antwort)


# --- Paket --------------------------------------------------------------------------


def test_paket_enthaelt_nur_die_aenderungen_an_zugeordneten_klassen(baseline):
    szenario = _szenario(
        baseline, _aenderung(baseline, "Ausleihe.java"), _aenderung(baseline, "Katalog.java", SUCHE)
    )

    uc5 = _paket(baseline, szenario, "UC5")
    uc4 = _paket(baseline, szenario, "UC4")

    assert [c.class_id for c in uc5.changes] == ["Katalog.java"]
    assert [c.class_id for c in uc4.changes] == ["Ausleihe.java"]


def test_use_case_wird_gegen_alle_seine_relevanten_aenderungen_geprueft(baseline):
    """Konzept 4.4: Zwei einzeln plausible Aenderungen koennen erst gemeinsam eine
    Erfolgsbedingung verletzen. UC1 gehoert zu Ausleihe.java und Buch.java."""
    szenario = _szenario(
        baseline, _aenderung(baseline, "Ausleihe.java"), _aenderung(baseline, "Buch.java")
    )

    paket = _paket(baseline, szenario, "UC1")

    assert sorted(c.class_id for c in paket.changes) == ["Ausleihe.java", "Buch.java"]


def test_paket_traegt_titel_und_text_des_use_cases(baseline):
    szenario = _szenario(baseline, _aenderung(baseline, "Katalog.java", SUCHE))

    paket = _paket(baseline, szenario, "UC5")

    assert paket.title == baseline.use_cases[UseCaseId("UC5")].title
    assert paket.text == baseline.use_cases[UseCaseId("UC5")].text


def test_prompt_nennt_use_case_methode_und_beide_fassungen(baseline):
    aenderung = _aenderung(baseline, "Katalog.java", SUCHE)
    paket = _paket(baseline, _szenario(baseline, aenderung), "UC5")

    prompt = render_use_case_prompt(paket)

    assert "UC5" in prompt
    assert baseline.use_cases[UseCaseId("UC5")].text in prompt
    assert "Katalog.java#suche(String)" in prompt
    assert aenderung.before in prompt
    assert "// geaendert" in prompt


def test_prompt_laesst_die_frage_ob_die_aenderung_gewollt_ist_beim_anwender(baseline):
    """Konzept 4.7: Eine Anpassung des Anforderungstextes ist nicht automatisch die
    bevorzugte Loesung."""
    paket = _paket(baseline, _szenario(baseline, _aenderung(baseline, "Ausleihe.java")), "UC1")

    prompt = render_use_case_prompt(paket)

    assert "entscheidet der Anwender" in prompt
    assert "keine Garantie" in prompt
    assert "insufficient_information" in prompt


# --- Antwortpruefung -------------------------------------------------------------------


def test_gueltige_antwort_mit_abweichung_wird_gelesen():
    text = _antwort(
        status="possible_deviation",
        affected_passage="Erfolgsbedingung",
        reason="Die Trefferliste ist jetzt leer",
        proposed_text="Neuer Text",
    )

    antwort = check_assessment(text)

    assert antwort.state is AnswerState.ANSWERED
    assert antwort.assessment.status is DeviationStatus.POSSIBLE_DEVIATION
    assert antwort.assessment.proposed_text == "Neuer Text"
    assert antwort.assessment_problems == ()


def test_textvorschlag_ist_optional():
    text = _antwort(status="possible_deviation", affected_passage="Schritt 3", reason="anders")

    antwort = check_assessment(text)

    assert antwort.assessment.proposed_text is None
    assert antwort.assessment_problems == ()


def test_abweichung_ohne_stelle_oder_begruendung_ist_unvollstaendig():
    ohne_begruendung = _antwort(status="possible_deviation", affected_passage="Schritt 3")
    ohne_stelle = _antwort(status="possible_deviation", reason="anders")

    assert check_assessment(ohne_begruendung).assessment_problems == (AssessmentProblem.INCOMPLETE,)
    assert check_assessment(ohne_stelle).assessment_problems == (AssessmentProblem.INCOMPLETE,)


def test_keine_erkennbare_abweichung_bleibt_ein_eigener_status():
    antwort = check_assessment(_antwort(status="no_deviation_visible", reason="nichts gefunden"))

    assert antwort.assessment.status is DeviationStatus.NO_DEVIATION_VISIBLE


def test_unzureichende_information_und_fehlender_kontext_werden_erfasst():
    text = _antwort(status="insufficient_information", missing_context=["Aufrufer fehlen"])

    antwort = check_assessment(text)

    assert antwort.assessment.status is DeviationStatus.INSUFFICIENT_INFORMATION
    assert antwort.missing_context == ("Aufrufer fehlen",)


def test_json_im_codeblock_wird_gelesen():
    antwort = check_assessment("Hier:\n```json\n" + _antwort() + "\n```")

    assert antwort.state is AnswerState.ANSWERED


@pytest.mark.parametrize(
    "text",
    [
        "Das kann ich nicht beurteilen.",
        "{ kein json }",
        json.dumps({"ergebnis": "gut"}),
        _antwort(status="vielleicht"),
        _antwort(assumptions="keine Liste"),
    ],
)
def test_unlesbare_antwort_bleibt_offen(text):
    antwort = check_assessment(text)

    assert antwort.state is AnswerState.INVALID_FORMAT
    assert antwort.problems
    assert antwort.assessment is None


# --- Modellaufruf und Lauf ----------------------------------------------------------------


def test_analyse_haelt_prompt_rohantwort_und_zeitpunkte_fest(baseline):
    paket = _paket(baseline, _szenario(baseline, _aenderung(baseline, "Ausleihe.java")), "UC1")
    mock = MockProvider(_antwort())

    analyse = analyze_use_case(mock, paket)

    assert mock.prompts == [analyse.prompt]
    assert analyse.raw_response == _antwort()
    assert analyse.use_case_id == "UC1"
    assert analyse.prompt_version
    assert analyse.requested_at <= analyse.finished_at


def test_gescheiterter_aufruf_ergibt_keine_antwort_und_keine_entwarnung(baseline):
    class Ausfall:
        name = "ausfall"
        settings: dict = {}

        def complete(self, prompt: str) -> str:
            raise LlmError("Zeitueberschreitung")

    paket = _paket(baseline, _szenario(baseline, _aenderung(baseline, "Ausleihe.java")), "UC1")

    analyse = analyze_use_case(Ausfall(), paket)

    assert analyse.raw_response is None
    assert analyse.answer.state is AnswerState.NO_ANSWER
    assert analyse.answer.assessment is None
    assert "Zeitueberschreitung" in analyse.answer.problems[0]


def test_lauf_fragt_das_modell_einmal_je_kandidat_use_case(baseline):
    mock = MockProvider(_antwort())
    szenario = _szenario(baseline, _aenderung(baseline, "Ausleihe.java"))

    lauf = run_backward_analysis(baseline, szenario, mock)

    assert [r.use_case_id for r in lauf.results] == ["UC1", "UC2", "UC4"]
    assert len(mock.prompts) == 3
    assert lauf.unassignable_class_ids == ()


def test_lauf_nennt_klassen_ohne_zuordnung_als_nicht_zuordenbar(baseline):
    """Konzept 4.7: Eine geaenderte Klasse ohne Zuordnung ist nicht zuordenbar,
    nicht unbeeintraechtigt."""
    mock = MockProvider(_antwort())
    szenario = _szenario(baseline, _aenderung(baseline, "Konfiguration.java"))

    lauf = run_backward_analysis(baseline, szenario, mock)

    assert lauf.results == ()
    assert lauf.unassignable_class_ids == ("Konfiguration.java",)
    assert mock.prompts == []


def test_jeder_lauf_hat_eine_eigene_kennung(baseline):
    szenario = _szenario(baseline, _aenderung(baseline, "Ausleihe.java"))
    mock = MockProvider(_antwort())

    erster = run_backward_analysis(baseline, szenario, mock)
    zweiter = run_backward_analysis(baseline, szenario, mock)

    assert erster.run_id != zweiter.run_id
    assert erster.provider_name == "mock"
