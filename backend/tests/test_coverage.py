"""Abdeckungsanzeige und Abschluss (Konzept 4.8 und 4.12).

Im Mittelpunkt steht, dass die vier Zustaende getrennt bleiben und keiner zur
Entwarnung wird: nicht zugeordnet, nicht verarbeitet, nicht beurteilbar und
"kein Bedarf im betrachteten Kontext erkennbar".
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cia.domain.ids import ClassId, ScenarioId
from cia.llm.mock import MockProvider
from cia.llm.provider import LlmError
from cia.llm.run import AnalysisRun, ClassResult
from cia.review.coverage import OpenKind, compute_coverage
from conftest import api_client, make_baseline, neues_szenario
from test_decisions import ANTWORT_MIT_VORSCHLAG, ANTWORT_OHNE_VORSCHLAG


def _lauf(client, sid):
    return client.post(f"/api/scenarios/{sid}/analyses").json()


def _abdeckung(client, sid) -> dict:
    return client.get(f"/api/scenarios/{sid}/coverage").json()


def _arten(abdeckung: dict) -> list[str]:
    return [i["kind"] for i in abdeckung["coverage"]["open_items"]]


def _entscheide(client, sid, lauf, kind, class_id="Katalog.java"):
    return client.post(
        f"/api/scenarios/{sid}/decisions",
        json={"run_id": lauf["run_id"], "subject_id": class_id, "entry_index": 0, "kind": kind},
    )


def _antwort_zu_allen_methoden(client, class_id: str) -> str:
    """Eine Antwort, die jede Methode der Klasse mit 'kein Bedarf erkennbar' beurteilt."""
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    methoden = client.get(f"/api/baselines/{baseline_id}/classes/{class_id}").json()["methods"]
    eintraege = []
    for methode in methoden:
        signatur = methode["ref"]["signature"]
        kennung = f"{signatur['name']}({', '.join(signatur['parameter_types'])})"
        eintraege.append(
            {
                "target_kind": "method",
                "target": kennung,
                "status": "no_change_visible",
                "use_case_passage": "",
                "reason": "im Kontext nichts erkennbar",
                "proposal": None,
            }
        )
    return json.dumps({"entries": eintraege})


# --- Zaehlwerte -------------------------------------------------------------------------


def test_stufen_werden_getrennt_gezaehlt(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    zaehlwerte = _abdeckung(client, sid)["coverage"]["counts"]

    assert zaehlwerte["imported_classes"] == 8
    assert zaehlwerte["candidate_classes"] == 2
    assert zaehlwerte["prepared_classes"] == 2
    assert zaehlwerte["analyzed_classes"] == 2


def test_standardmock_laesst_alle_methoden_als_offene_faelle_stehen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    assert abdeckung["counts"]["unanswered_methods"] == 11
    assert set(_arten({"coverage": abdeckung})) == {"unanswered_method"}
    assert len(abdeckung["open_items"]) == 11


def test_aenderung_ohne_zuordnung_ist_nicht_zugeordnet(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC6")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    assert abdeckung["counts"]["candidate_classes"] == 0
    assert [(i["kind"], i["ref"]) for i in abdeckung["open_items"]] == [("not_assigned", "UC6")]


def test_ausgefallenes_modell_ist_aufbereitet_aber_nicht_analysiert(fixture_root):
    """Konzept 4.12: aufbereitete und tatsaechlich analysierte Artefakte werden
    getrennt gezaehlt. Die Klassen wurden aufbereitet, aber nie beantwortet."""

    class Ausfall:
        name = "ausfall"
        settings: dict = {}

        def complete(self, prompt: str) -> str:
            raise LlmError("Zeitueberschreitung")

    client = api_client(fixture_root, Ausfall())
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    assert abdeckung["counts"]["prepared_classes"] == 2
    assert abdeckung["counts"]["analyzed_classes"] == 0
    assert [i["kind"] for i in abdeckung["open_items"]] == ["not_processed", "not_processed"]
    assert "Zeitueberschreitung" in abdeckung["open_items"][0]["detail"]


def test_unlesbare_antwort_ist_nicht_verarbeitet(fixture_root):
    client = api_client(fixture_root, MockProvider("Das weiss ich nicht."))
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    assert abdeckung["counts"]["analyzed_classes"] == 0
    assert set(i["kind"] for i in abdeckung["open_items"]) == {"not_processed"}


def test_kein_bedarf_erkennbar_wird_gezaehlt_ist_aber_kein_offener_fall(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_OHNE_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    # Fuer Katalog.java benennt der Eintrag suche(String), fuer Buch.java gibt es
    # die Methode nicht. Dort ist der Eintrag ungueltig: Er zaehlt nicht als
    # "kein Bedarf erkennbar", sondern bleibt als Problem offen.
    assert abdeckung["counts"]["no_change_visible"] == 1
    verweise = [i["ref"] for i in abdeckung["open_items"] if i["kind"] == "entry_with_problem"]
    assert verweise == ["Buch.java: suche(String)"]
    assert all("no_change" not in i["kind"] for i in abdeckung["open_items"])


def test_nicht_beurteilbar_ist_ein_offener_fall(fixture_root):
    antwort = json.dumps(
        {
            "entries": [
                {
                    "target_kind": "class",
                    "target": "Attribut buecher",
                    "status": "not_assessable",
                    "use_case_passage": "",
                    "reason": "Aufrufer fehlen",
                    "proposal": None,
                }
            ]
        }
    )
    client = api_client(fixture_root, MockProvider(antwort))
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    abdeckung = _abdeckung(client, sid)["coverage"]

    assert abdeckung["counts"]["not_assessable"] == 2
    gefunden = [i for i in abdeckung["open_items"] if i["kind"] == "not_assessable"]
    assert gefunden[0]["detail"] == "Aufrufer fehlen"


def test_vorschlaege_werden_nach_entscheidung_gezaehlt(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_MIT_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    lauf = _lauf(client, sid)

    vorher = _abdeckung(client, sid)["coverage"]["counts"]
    _entscheide(client, sid, lauf, "accepted")
    _entscheide(client, sid, lauf, "rejected", class_id="Buch.java")
    nachher = _abdeckung(client, sid)["coverage"]["counts"]

    assert (vorher["proposals"], vorher["proposals_undecided"]) == (2, 2)
    assert nachher["proposals_accepted"] == 1
    assert nachher["proposals_rejected"] == 1
    assert nachher["proposals_undecided"] == 0


def test_zurueckgestellter_vorschlag_bleibt_ein_offener_fall(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_MIT_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    lauf = _lauf(client, sid)
    _entscheide(client, sid, lauf, "deferred")

    abdeckung = _abdeckung(client, sid)

    assert "proposal_deferred" in _arten(abdeckung)
    assert abdeckung["coverage"]["counts"]["proposals_deferred"] == 1


def test_nur_die_letzte_entscheidung_je_vorschlag_zaehlt(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_MIT_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    lauf = _lauf(client, sid)
    _entscheide(client, sid, lauf, "rejected")
    _entscheide(client, sid, lauf, "accepted")

    zaehlwerte = _abdeckung(client, sid)["coverage"]["counts"]

    assert zaehlwerte["proposals_accepted"] == 1
    assert zaehlwerte["proposals_rejected"] == 0


def test_vorschlag_mit_problem_bleibt_offen_bis_er_beurteilt_ist(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_MIT_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    lauf = _lauf(client, sid)

    offen = [i for i in _abdeckung(client, sid)["coverage"]["open_items"] if i["ref"].startswith("Buch.java: ")]
    _entscheide(client, sid, lauf, "rejected", class_id="Buch.java")
    danach = [i for i in _abdeckung(client, sid)["coverage"]["open_items"] if i["ref"].startswith("Buch.java: ")]

    assert offen[0]["kind"] == "proposal_undecided"
    assert "unknown_method" in offen[0]["detail"]
    assert danach == []


def test_nicht_verarbeitete_klasse_ohne_paket_ist_ein_offener_fall():
    """Konzept 4.12: Eine nicht geparste Klasse bleibt unabhaengig vom Ergebnis der
    anderen sichtbar."""
    baseline = make_baseline([("UC1", "K.java")])
    jetzt = datetime.now(timezone.utc)
    lauf = AnalysisRun(
        run_id="r1",
        scenario_id=ScenarioId("s"),
        baseline_id=baseline.id,
        started_at=jetzt,
        finished_at=jetzt,
        provider_name="mock",
        provider_settings={},
        prompt_version="v",
        results=(ClassResult(ClassId("K.java"), "Klasse wurde nicht verarbeitet", None),),
        unresolved=(),
    )

    abdeckung = compute_coverage(baseline, lauf, [])

    assert abdeckung.counts["candidate_classes"] == 1
    assert abdeckung.counts["prepared_classes"] == 0
    assert [i.kind for i in abdeckung.open_items] == [OpenKind.NOT_PROCESSED]


def test_abdeckung_ohne_analyselauf_wird_abgewiesen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    assert client.get(f"/api/scenarios/{sid}/coverage").status_code == 409
    assert client.get("/api/scenarios/gibt-es-nicht/coverage").status_code == 404


# --- Abschluss ----------------------------------------------------------------------------


def test_abschluss_mit_offenen_faellen_braucht_bestaetigung(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    antwort = client.post(f"/api/scenarios/{sid}/close", json={})

    assert antwort.status_code == 409
    assert len(antwort.json()["detail"]["open_items"]) == 11
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "ready_for_review"


def test_abschluss_mit_bestaetigung_aber_ohne_begruendung_wird_abgewiesen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    antwort = client.post(f"/api/scenarios/{sid}/close", json={"acknowledge_open_items": True})

    assert antwort.status_code == 422


def test_abschluss_mit_offenen_faellen_haelt_sie_fest_und_sie_bleiben_sichtbar(fixture_root):
    """Konzept 4.8: Auch bei abgeschlossenem Szenario bleibt sichtbar, welche
    Fragen nicht geklaert wurden."""
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)

    antwort = client.post(
        f"/api/scenarios/{sid}/close",
        json={"acknowledge_open_items": True, "note": "Mock ohne Bewertung, nur zum Testen"},
    )

    assert antwort.status_code == 200
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "closed"
    abdeckung = _abdeckung(client, sid)
    assert abdeckung["closure"]["open_items_acknowledged"] is True
    assert abdeckung["closure"]["note"] == "Mock ohne Bewertung, nur zum Testen"
    assert len(abdeckung["closure"]["open_items"]) == 11
    assert len(abdeckung["coverage"]["open_items"]) == 11


def test_abschluss_ohne_offene_faelle_braucht_keine_bestaetigung(fixture_root):
    """Mitglied.java ist die einzige Klasse von UC3. Beurteilt das Modell alle
    ihre Methoden, bleibt nichts offen. 'Kein Bedarf' ist dabei kein offener Fall,
    aber auch keine Garantie: Die Zahl steht im Abschluss."""
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC3")
    client.app.state.provider = MockProvider(_antwort_zu_allen_methoden(client, "Mitglied.java"))
    _lauf(client, sid)

    assert _abdeckung(client, sid)["coverage"]["open_items"] == []
    antwort = client.post(f"/api/scenarios/{sid}/close", json={})

    assert antwort.status_code == 200
    assert antwort.json()["open_items_acknowledged"] is False
    assert antwort.json()["note"] is None


def test_abgeschlossenes_szenario_nimmt_keine_entscheidungen_und_keine_analysen_an(fixture_root):
    client = api_client(fixture_root, MockProvider(ANTWORT_MIT_VORSCHLAG))
    sid = neues_szenario(client, "UC5")
    lauf = _lauf(client, sid)
    client.post(f"/api/scenarios/{sid}/close", json={"acknowledge_open_items": True, "note": "Test"})

    assert _entscheide(client, sid, lauf, "accepted").status_code == 409
    assert client.post(f"/api/scenarios/{sid}/analyses").status_code == 409
    assert client.post(f"/api/scenarios/{sid}/discard").status_code == 409


def test_szenario_ohne_analyse_laesst_sich_nicht_abschliessen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    assert client.post(f"/api/scenarios/{sid}/close", json={}).status_code == 409


def test_abschluss_steht_im_protokoll(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    _lauf(client, sid)
    client.post(f"/api/scenarios/{sid}/close", json={"acknowledge_open_items": True, "note": "Test"})

    eintraege = client.get(f"/api/scenarios/{sid}/protocol").json()

    abschluss = next(e for e in eintraege if e["kind"] == "scenario_closed")
    assert abschluss["data"]["closure"]["note"] == "Test"
    assert abschluss["data"]["counts"]["unanswered_methods"] == 11
    assert eintraege[-1]["data"]["to"] == "closed"


def test_unbekanntes_szenario_beim_abschluss_liefert_404(fixture_root):
    client = api_client(fixture_root)

    assert client.post("/api/scenarios/gibt-es-nicht/close", json={}).status_code == 404
