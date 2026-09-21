"""Analysepaket, Antwortpruefung und Modellaufruf (Konzept 4.5 und 4.10).

Alle Tests laufen ohne echtes Modell, nur mit dem Mock. Geprueft wird die
technische Seite: Was geht ins Paket, was passiert mit einer Antwort. Ob ein
Vorschlag fachlich stimmt, ist nicht Sache dieser Tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cia.analysis.structural import select_forward
from cia.domain.artifacts import (
    JavaClass,
    JavaMethod,
    MethodRef,
    MethodSignature,
    SourceRange,
    UseCase,
)
from cia.domain.baseline import Baseline
from cia.domain.ids import BaselineId, ClassId, UseCaseId
from cia.domain.links import TraceGraph, TraceLink
from cia.domain.scenario import ChangeKind, Direction, RequirementChange, Scenario
from cia.importing.project import import_project
from cia.llm.analyze import analyze_class
from cia.llm.answer import AnswerState, EntryProblem, Status, TargetKind, check_answer
from cia.llm.mock import MockProvider
from cia.llm.package import ClassPackage, PackageProblem, build_class_package, render_prompt
from cia.llm.provider import LlmError
from cia.llm.run import run_forward_analysis
from conftest import scenario_id


@pytest.fixture(scope="module")
def baseline(fixture_root) -> Baseline:
    return import_project(fixture_root).baseline


def _szenario(baseline: Baseline, *aenderungen: RequirementChange) -> Scenario:
    return Scenario(
        id=scenario_id(),
        baseline_id=baseline.id,
        title="t",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=tuple(aenderungen),
    )


def _paket(baseline: Baseline, class_id: str, *aenderungen: RequirementChange):
    """Baut das Paket fuer eine Klasse, wie es die Pipeline tun wuerde."""
    scenario = _szenario(baseline, *aenderungen)
    auswahl = select_forward(baseline, scenario)
    kandidat = next(c for c in auswahl.candidates if c.class_id == class_id)
    return build_class_package(baseline, scenario, kandidat)


def _deaktivieren(use_case_id: str) -> RequirementChange:
    return RequirementChange(ChangeKind.DEACTIVATE, UseCaseId(use_case_id))


@pytest.fixture(scope="module")
def katalog_paket(baseline) -> ClassPackage:
    paket = _paket(baseline, "Katalog.java", _deaktivieren("UC5"))
    assert isinstance(paket, ClassPackage)
    return paket


# --- Hilfen fuer Antworten -------------------------------------------------


def _eintrag(target: str, status: str = "no_change_visible", kind: str = "method", **felder):
    eintrag = {
        "target_kind": kind,
        "target": target,
        "status": status,
        "use_case_passage": "",
        "reason": "",
        "proposal": None,
    }
    eintrag.update(felder)
    return eintrag


def _antwort(*eintraege, **extra) -> str:
    return json.dumps({"entries": list(eintraege), **extra})


def _vorschlag(target: str) -> dict:
    return _eintrag(
        target,
        "change_proposed",
        use_case_passage="Der Anwender gibt einen Teil des Titels ein",
        reason="Der Ablauf entfaellt",
        proposal="Methode entfernen",
    )


# --- Analysepaket -------------------------------------------------------------


def test_paket_enthaelt_alle_methoden_der_klasse(baseline, katalog_paket):
    ids = {str(m.signature) for m in katalog_paket.methods}

    assert "suche(String)" in ids
    assert "suche(String, String)" in ids
    assert len(katalog_paket.methods) == len(baseline.classes[ClassId("Katalog.java")].methods)


def test_paket_traegt_die_ausloesende_aenderung_mit_bisherigem_text(baseline, katalog_paket):
    aenderung = katalog_paket.changes[0]

    assert aenderung.use_case_id == "UC5"
    assert aenderung.kind is ChangeKind.DEACTIVATE
    assert aenderung.old_text == baseline.use_cases[UseCaseId("UC5")].text
    assert aenderung.new_text is None
    assert aenderung.is_trigger is True


def test_paket_traegt_weiter_geltende_use_cases_als_kontext(baseline):
    """Buch.java gehoert auch zu UC1 und UC2. Sie muessen erhalten bleiben."""
    paket = _paket(baseline, "Buch.java", _deaktivieren("UC5"))

    assert isinstance(paket, ClassPackage)
    assert [u.use_case_id for u in paket.context_use_cases] == ["UC1", "UC2"]


def test_paket_enthaelt_auch_aenderungen_die_nicht_zu_dieser_klasse_fuehren(baseline):
    """Konzept 4.11: Das Modell soll den gemeinsamen Zielzustand kennen."""
    paket = _paket(baseline, "Katalog.java", _deaktivieren("UC5"), _deaktivieren("UC3"))

    assert isinstance(paket, ClassPackage)
    ausloeser = {c.use_case_id: c.is_trigger for c in paket.changes}
    assert ausloeser == {"UC5": True, "UC3": False}


def test_prompt_nennt_jede_methodenkennung_und_den_quelltext(katalog_paket):
    prompt = render_prompt(katalog_paket)

    for methode in katalog_paket.methods:
        assert str(methode.signature) in prompt
        assert methode.source in prompt
    assert "UC5" in prompt


def test_prompt_verlangt_dass_fehlender_kontext_nicht_geraten_wird(katalog_paket):
    prompt = render_prompt(katalog_paket)

    assert "not_assessable" in prompt
    assert "keine Garantie" in prompt


def _klasse(class_id: str, methoden=(), parsed=True) -> JavaClass:
    return JavaClass(
        id=ClassId(class_id),
        baseline_id=BaselineId("b"),
        file_name=class_id,
        relative_path=class_id,
        source="",
        methods=tuple(methoden),
        parsed=parsed,
        parse_error=None if parsed else "kaputt",
    )


def _methode(name: str, start: int) -> JavaMethod:
    ref = MethodRef(
        baseline_id=BaselineId("b"),
        class_id=ClassId("K.java"),
        signature=MethodSignature(name, ()),
        source_range=SourceRange(start, start, start, start + 1),
    )
    return JavaMethod(ref=ref, source=f"void {name}() {{}}")


def _baseline_mit(klasse: JavaClass) -> Baseline:
    use_case = UseCase(UseCaseId("UC1"), BaselineId("b"), "t", "text")
    return Baseline.create(
        BaselineId("b"),
        "test",
        {use_case.id: use_case},
        {klasse.id: klasse},
        TraceGraph([TraceLink(use_case.id, klasse.id)]),
    )


def test_nicht_geparste_klasse_ergibt_ein_problem_statt_eines_pakets():
    """Konzept 4.12: Eine nicht verarbeitete Klasse bleibt sichtbar."""
    klasse = _klasse("K.java", [_methode("a", 1)], parsed=False)

    ergebnis = _paket(_baseline_mit(klasse), "K.java", _deaktivieren("UC1"))

    assert isinstance(ergebnis, PackageProblem)
    assert "nicht verarbeitet" in ergebnis.reason


def test_doppelte_methodenkennung_ergibt_ein_problem_statt_eines_pakets():
    klasse = _klasse("K.java", [_methode("a", 1), _methode("a", 5)])

    ergebnis = _paket(_baseline_mit(klasse), "K.java", _deaktivieren("UC1"))

    assert isinstance(ergebnis, PackageProblem)
    assert "a()" in ergebnis.reason


# --- Antwortpruefung -----------------------------------------------------------


def test_gueltige_antwort_ordnet_bestehende_methoden_zu(katalog_paket):
    antwort = check_answer(katalog_paket, _antwort(_vorschlag("suche(String)")))

    assert antwort.state is AnswerState.ANSWERED
    eintrag = antwort.entries[0]
    assert eintrag.problems == ()
    assert eintrag.method_ref is not None
    assert eintrag.method_ref.class_id == "Katalog.java"
    assert eintrag.method_ref.baseline_id == katalog_paket.baseline_id
    assert eintrag.method_ref.signature.parameter_types == ("String",)


def test_unbekannte_methode_bleibt_kenntlich_und_wird_nicht_einer_aehnlichen_zugeordnet(
    katalog_paket,
):
    """Konzept 4.10: Keine automatische Aehnlichkeitssuche. 'suche(String,String)'
    ohne Leerzeichen ist nicht dieselbe Kennung wie 'suche(String, String)'."""
    antwort = check_answer(katalog_paket, _antwort(_eintrag("suche(String,String)")))

    eintrag = antwort.entries[0]
    assert eintrag.method_ref is None
    assert eintrag.problems == (EntryProblem.UNKNOWN_METHOD,)


def test_neue_methode_wird_als_neues_element_gefuehrt(katalog_paket):
    antwort = check_answer(
        katalog_paket, _antwort(_eintrag("sucheNachAutor(String)", kind="new_method"))
    )

    eintrag = antwort.entries[0]
    assert eintrag.entry.target_kind is TargetKind.NEW_METHOD
    assert eintrag.method_ref is None
    assert eintrag.problems == ()


def test_als_neu_gemeldete_methode_mit_vorhandener_kennung_wird_beanstandet(katalog_paket):
    antwort = check_answer(
        katalog_paket, _antwort(_eintrag("suche(String)", kind="new_method"))
    )

    assert antwort.entries[0].problems == (EntryProblem.ALREADY_EXISTS,)


def test_nicht_erwaehnte_methoden_gelten_nicht_als_unveraendert(katalog_paket):
    """Konzept 4.10: Eine nicht erwaehnte Methode darf nicht automatisch als
    unveraendert gelten. Sie bleibt offen."""
    antwort = check_answer(katalog_paket, _antwort(_eintrag("suche(String)")))

    offen = {str(ref.signature) for ref in antwort.unanswered_methods}
    assert "suche(String)" not in offen
    assert len(offen) == len(katalog_paket.methods) - 1
    assert "suche(String, String)" in offen


def test_aenderungsvorschlag_ohne_soll_zustand_ist_unvollstaendig(katalog_paket):
    unvollstaendig = _eintrag("suche(String)", "change_proposed", reason="weil")

    antwort = check_answer(katalog_paket, _antwort(unvollstaendig))

    assert antwort.entries[0].problems == (EntryProblem.INCOMPLETE,)


def test_doppelter_eintrag_zur_selben_methode_wird_beanstandet(katalog_paket):
    antwort = check_answer(
        katalog_paket,
        _antwort(_vorschlag("suche(String)"), _eintrag("suche(String)")),
    )

    assert antwort.entries[0].problems == ()
    assert antwort.entries[1].problems == (EntryProblem.DUPLICATE,)


def test_klassenstelle_braucht_keine_methodenreferenz(katalog_paket):
    """Konzept 4.5: Auswirkungen auf Attribute bleiben als Hinweis auf
    Klassenebene erhalten."""
    antwort = check_answer(
        katalog_paket, _antwort(_eintrag("Attribut buecher", "not_assessable", kind="class"))
    )

    eintrag = antwort.entries[0]
    assert eintrag.method_ref is None
    assert eintrag.problems == ()
    assert eintrag.entry.status is Status.NOT_ASSESSABLE


def test_annahmen_und_fehlender_kontext_werden_getrennt_erfasst(katalog_paket):
    antwort = check_answer(
        katalog_paket,
        _antwort(assumptions=["Nur UC5 ist betroffen"], missing_context=["Aufrufer fehlen"]),
    )

    assert antwort.assumptions == ("Nur UC5 ist betroffen",)
    assert antwort.missing_context == ("Aufrufer fehlen",)


def test_json_im_codeblock_wird_gelesen(katalog_paket):
    text = "Hier ist die Antwort:\n```json\n" + _antwort(_eintrag("suche(String)")) + "\n```"

    antwort = check_answer(katalog_paket, text)

    assert antwort.state is AnswerState.ANSWERED
    assert len(antwort.entries) == 1


@pytest.mark.parametrize(
    "text",
    [
        "Das kann ich leider nicht beurteilen.",
        "{ das ist kein json }",
        json.dumps({"ergebnis": []}),
        _antwort(_eintrag("suche(String)", status="vielleicht")),
        _antwort(_eintrag("suche(String)", kind="etwas")),
        _antwort(_eintrag("")),
        _antwort(assumptions="keine Liste"),
    ],
)
def test_unlesbare_antwort_laesst_alle_methoden_offen(katalog_paket, text):
    """Konzept 4.5: Was sich nicht zuordnen laesst, bleibt offen und wird nicht
    zur Entwarnung."""
    antwort = check_answer(katalog_paket, text)

    assert antwort.state is AnswerState.INVALID_FORMAT
    assert antwort.problems
    assert antwort.entries == ()
    assert len(antwort.unanswered_methods) == len(katalog_paket.methods)


# --- Modellaufruf -----------------------------------------------------------------


def test_mock_liefert_feste_antwort_und_merkt_sich_den_prompt(katalog_paket):
    antwort_text = _antwort(_vorschlag("suche(String)"))
    mock = MockProvider(antwort_text)

    analyse = analyze_class(mock, katalog_paket)

    assert mock.prompts == [analyse.prompt]
    assert analyse.raw_response == antwort_text
    assert analyse.provider_name == "mock"
    assert analyse.answer.state is AnswerState.ANSWERED


def test_analyse_haelt_prompt_version_und_klasse_fest(katalog_paket):
    analyse = analyze_class(MockProvider(_antwort()), katalog_paket)

    assert analyse.class_id == "Katalog.java"
    assert analyse.prompt_version


def test_unlesbare_antwort_bleibt_als_rohtext_erhalten(katalog_paket):
    """Konzept 4.13: Die tatsaechlich erhaltene Antwort wird festgehalten."""
    analyse = analyze_class(MockProvider("kein json"), katalog_paket)

    assert analyse.raw_response == "kein json"
    assert analyse.answer.state is AnswerState.INVALID_FORMAT


class _AusfallenderAnbieter:
    name = "ausfall"
    settings: dict = {}

    def complete(self, prompt: str) -> str:
        raise LlmError("Zeitueberschreitung")


def test_gescheiterter_aufruf_ergibt_keine_antwort_und_keine_entwarnung(katalog_paket):
    analyse = analyze_class(_AusfallenderAnbieter(), katalog_paket)

    assert analyse.raw_response is None
    assert analyse.answer.state is AnswerState.NO_ANSWER
    assert "Zeitueberschreitung" in analyse.answer.problems[0]
    assert len(analyse.answer.unanswered_methods) == len(katalog_paket.methods)


# --- Analyselauf -------------------------------------------------------------------


def test_lauf_fragt_das_modell_einmal_je_kandidatenklasse(baseline):
    mock = MockProvider(_antwort())

    lauf = run_forward_analysis(baseline, _szenario(baseline, _deaktivieren("UC5")), mock)

    assert [r.class_id for r in lauf.results] == ["Buch.java", "Katalog.java"]
    assert len(mock.prompts) == 2
    assert all(r.analysis is not None and r.not_processed_reason is None for r in lauf.results)


def test_lauf_nennt_aenderungen_ohne_zuordnung(baseline):
    """Konzept 4.3: Eine leere Kandidatenmenge ist keine Entwarnung. UC6 hat
    keine Zuordnung und taucht deshalb als offene Aenderung auf."""
    mock = MockProvider(_antwort())

    lauf = run_forward_analysis(baseline, _szenario(baseline, _deaktivieren("UC6")), mock)

    assert lauf.results == ()
    assert [u.use_case_id for u in lauf.unresolved] == ["UC6"]
    assert mock.prompts == []


def test_lauf_haelt_nicht_verarbeitete_klasse_fest_und_fragt_das_modell_nicht():
    """Konzept 4.12: Eine nicht geparste Klasse bleibt sichtbar."""
    klasse = _klasse("K.java", [_methode("a", 1)], parsed=False)
    baseline = _baseline_mit(klasse)
    mock = MockProvider(_antwort())

    lauf = run_forward_analysis(baseline, _szenario(baseline, _deaktivieren("UC1")), mock)

    ergebnis = lauf.results[0]
    assert ergebnis.analysis is None
    assert "nicht verarbeitet" in ergebnis.not_processed_reason
    assert mock.prompts == []


def test_jeder_lauf_hat_eine_eigene_kennung(baseline):
    szenario = _szenario(baseline, _deaktivieren("UC5"))
    mock = MockProvider(_antwort())

    erster = run_forward_analysis(baseline, szenario, mock)
    zweiter = run_forward_analysis(baseline, szenario, mock)

    assert erster.run_id != zweiter.run_id
    assert erster.provider_name == "mock"
    assert erster.prompt_version


# --- Modulgrenze -------------------------------------------------------------------


def test_analysis_haengt_von_keiner_modellanbindung_ab():
    """CLAUDE.md: Die Trennung zwischen deterministischer Auswahl und
    LLM-Bewertung ist eine Modulgrenze. ``analysis/`` darf ``llm/`` nicht
    importieren."""
    ordner = Path(__file__).resolve().parents[1] / "src" / "cia" / "analysis"
    dateien = sorted(ordner.glob("*.py"))
    assert dateien, "analysis/ nicht gefunden"

    for datei in dateien:
        for zeile in datei.read_text(encoding="utf-8").splitlines():
            if zeile.startswith(("import ", "from ")):
                assert "llm" not in zeile, f"{datei.name} importiert llm: {zeile}"
