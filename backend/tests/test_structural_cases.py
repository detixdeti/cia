"""Konkrete Auswahlfaelle am Beispielprojekt.

Waehrend ``test_structural_properties`` allgemeine Eigenschaften prueft, zeigen
die folgenden Tests die im Konzept beschriebenen Situationen an einer festen
Datenbasis. Insbesondere die Unterscheidung zwischen einer Klasse, der ein
aktiver Use Case bleibt, und einer, der keiner bleibt (Konzept 4.5).
"""

from __future__ import annotations

import pytest

from cia.analysis.structural import select_backward, select_forward
from cia.domain.ids import ClassId, UseCaseId
from cia.importing.project import import_project
from cia.domain.scenario import (
    ChangeKind,
    CodeChange,
    Direction,
    IllegalTransition,
    RequirementChange,
    Scenario,
    ScenarioState,
)


@pytest.fixture(scope="module")
def baseline(fixture_root):
    return import_project(fixture_root, label="bib-fixture").baseline


def deaktiviere(baseline, *use_case_ids: str) -> Scenario:
    return Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Deaktivierung",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=tuple(
            RequirementChange(ChangeKind.DEACTIVATE, UseCaseId(u)) for u in use_case_ids
        ),
    )


def test_deaktivierung_liefert_die_deklarierten_klassen(baseline):
    selection = select_forward(baseline, deaktiviere(baseline, "UC1"))

    assert selection.candidate_class_ids == {
        ClassId("AusleihService.java"),
        ClassId("Ausleihe.java"),
        ClassId("Buch.java"),
        ClassId("Mitglied.java"),
    }


def test_erhaltungskontext_nennt_die_verbleibenden_aktiven_use_cases(baseline):
    """Konzept 4.3: Weitere aktive Use Cases an einer gemeinsam genutzten Klasse
    erscheinen ausschliesslich als Erhaltungskontext und werden in dieser
    Richtung nie als betroffen markiert."""
    selection = select_forward(baseline, deaktiviere(baseline, "UC1"))
    kontext = {c.class_id: c.preservation_context_ids for c in selection.candidates}

    assert kontext[ClassId("Mitglied.java")] == {UseCaseId("UC3"), UseCaseId("UC4")}
    assert kontext[ClassId("Buch.java")] == {UseCaseId("UC2"), UseCaseId("UC5")}
    assert kontext[ClassId("AusleihService.java")] == {UseCaseId("UC2")}

    # Der geaenderte Use Case selbst gehoert nicht zum Erhaltungskontext.
    for ids in kontext.values():
        assert UseCaseId("UC1") not in ids


def test_klasse_ohne_verbleibenden_use_case_wird_nicht_als_loeschbar_markiert(baseline):
    """Konzept 4.5: Selbst wenn einer Klasse kein aktiver Use Case mehr
    zugeordnet ist, folgt daraus keine automatische Loeschfreigabe. Die
    Eigenschaft ist eine Anzeige fuer den Anwender, kein Kriterium."""
    selection = select_forward(baseline, deaktiviere(baseline, "UC5"))
    kandidaten = {c.class_id: c for c in selection.candidates}

    katalog = kandidaten[ClassId("Katalog.java")]
    assert katalog.preservation_context_ids == frozenset()
    assert katalog.has_remaining_use_cases is False

    # Buch.java bleibt dagegen ueber UC1 und UC2 belegt.
    buch = kandidaten[ClassId("Buch.java")]
    assert buch.has_remaining_use_cases is True


def test_mehrere_geaenderte_use_cases_werden_vereinigt(baseline):
    """Konzept 4.3: Bei mehreren geaenderten Use Cases wird die Vereinigung
    ihrer Nachbarschaften gebildet."""
    einzeln = select_forward(baseline, deaktiviere(baseline, "UC1")).candidate_class_ids
    zusammen = select_forward(
        baseline, deaktiviere(baseline, "UC1", "UC5")
    ).candidate_class_ids

    assert einzeln < zusammen
    assert ClassId("Katalog.java") in zusammen


def test_ausloeser_bleiben_je_kandidat_nachvollziehbar(baseline):
    """Das LLM darf die Herkunft der Kandidaten weder ersetzen noch verdecken
    (Konzept 4.3). Dafuer muss sie ueberhaupt mitgefuehrt werden."""
    selection = select_forward(baseline, deaktiviere(baseline, "UC1", "UC4"))
    ausloeser = {c.class_id: c.triggering_use_case_ids for c in selection.candidates}

    assert ausloeser[ClassId("Ausleihe.java")] == {UseCaseId("UC1"), UseCaseId("UC4")}
    assert ausloeser[ClassId("MahnungService.java")] == {UseCaseId("UC4")}
    assert ausloeser[ClassId("AusleihService.java")] == {UseCaseId("UC1")}


def test_use_case_ohne_zuordnung_meldet_offenen_fall(baseline):
    """Konzept 4.3: Die leere Kandidatenmenge bedeutet nicht, dass die
    Aenderung wirkungslos waere."""
    selection = select_forward(baseline, deaktiviere(baseline, "UC6"))

    assert selection.candidates == ()
    assert len(selection.unresolved) == 1
    assert selection.unresolved[0].use_case_id == UseCaseId("UC6")


def test_neuer_use_case_ohne_manuelle_auswahl_meldet_fehlende_zuordnung(baseline):
    """Konzept 4.3: Fehlt diese Eingabe, meldet das Werkzeug 'keine Zuordnung
    fuer die Analyse vorhanden'."""
    szenario = Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Ergaenzung",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=(
            RequirementChange(
                ChangeKind.ADD, UseCaseId("UC-neu"), target_text="Vormerkung anlegen"
            ),
        ),
    )
    selection = select_forward(baseline, szenario)

    assert selection.candidates == ()
    assert selection.unresolved[0].reason == "keine Zuordnung fuer die Analyse vorhanden"


def test_neuer_use_case_nutzt_die_manuellen_zuordnungen(baseline):
    """Konzept 4.3: Fuer einen neu angelegten Use Case wird dieselbe Auswahlregel
    auf die vom Anwender festgelegten Szenariozuordnungen angewendet. Der
    Ausgangsstand bleibt dabei unveraendert."""
    vorher = len(baseline.trace_graph)
    szenario = Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Ergaenzung",
        direction=Direction.REQUIREMENT_TO_CODE,
        requirement_changes=(
            RequirementChange(
                ChangeKind.ADD,
                UseCaseId("UC-neu"),
                target_text="Vormerkung anlegen",
                manual_class_ids=(ClassId("Buch.java"), ClassId("Mitglied.java")),
            ),
        ),
    )
    selection = select_forward(baseline, szenario)

    assert selection.candidate_class_ids == {
        ClassId("Buch.java"),
        ClassId("Mitglied.java"),
    }
    assert len(baseline.trace_graph) == vorher


def test_gegenrichtung_am_beispiel(baseline):
    """Konzept 4.6: Aus jeder geaenderten Klasse werden alle im Ausgangsstand
    zugeordneten Use Cases ermittelt."""
    szenario = Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Codeaenderung",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=(
            CodeChange(ClassId("Ausleihe.java"), before="alt", after="neu"),
        ),
    )
    selection = select_backward(baseline, szenario)

    assert selection.candidate_use_case_ids == {
        UseCaseId("UC1"),
        UseCaseId("UC2"),
        UseCaseId("UC4"),
    }


def test_gegenrichtung_fuehrt_doppelte_use_cases_zusammen(baseline):
    """Konzept 4.4: Der Kandidat wird einmal angezeigt, aber gegen die
    Gesamtheit der relevanten Aenderungen geprueft. Die ausloesenden Klassen
    bleiben deshalb gemeinsam erhalten."""
    szenario = Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Zwei Aenderungen",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=(
            CodeChange(ClassId("Ausleihe.java"), before="a", after="b"),
            CodeChange(ClassId("AusleihService.java"), before="a", after="b"),
        ),
    )
    selection = select_backward(baseline, szenario)
    kontext = {c.use_case_id: c.triggering_class_ids for c in selection.candidates}

    assert kontext[UseCaseId("UC1")] == {
        ClassId("Ausleihe.java"),
        ClassId("AusleihService.java"),
    }
    assert kontext[UseCaseId("UC4")] == {ClassId("Ausleihe.java")}


def test_geaenderte_klasse_ohne_zuordnung_ist_nicht_zuordenbar(baseline):
    szenario = Scenario(
        id="s",
        baseline_id=baseline.id,
        title="Codeaenderung",
        direction=Direction.CODE_TO_REQUIREMENT,
        code_changes=(
            CodeChange(ClassId("Konfiguration.java"), before="alt", after="neu"),
        ),
    )
    selection = select_backward(baseline, szenario)

    assert selection.candidates == ()
    assert selection.unassignable_class_ids == {ClassId("Konfiguration.java")}


def test_zustandsautomat_erlaubt_nur_vorgesehene_uebergaenge(baseline):
    """Konzept 4.8 legt die Zustaende fest. Ein Abschluss ohne vorherige
    Analyse ist nicht vorgesehen."""
    szenario = deaktiviere(baseline, "UC1")

    assert szenario.state is ScenarioState.CREATED
    with pytest.raises(IllegalTransition):
        szenario.transition_to(ScenarioState.CLOSED)

    szenario.transition_to(ScenarioState.STRUCTURALLY_CHECKED)
    szenario.transition_to(ScenarioState.ANALYSIS_RUNNING)
    szenario.transition_to(ScenarioState.READY_FOR_REVIEW)
    szenario.transition_to(ScenarioState.CLOSED)


def test_abbruch_ist_aus_jedem_offenen_zustand_zulaessig(baseline):
    """Konzept 4.13: Der Anwender muss ein Szenario verwerfen koennen, ohne
    einen vollstaendigen Soll-Zustand zu erzeugen."""
    szenario = deaktiviere(baseline, "UC1")
    szenario.transition_to(ScenarioState.STRUCTURALLY_CHECKED)
    szenario.transition_to(ScenarioState.DISCARDED)

    assert szenario.state is ScenarioState.DISCARDED
