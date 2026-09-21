"""Gegenrichtung ueber die Schnittstelle (F6, Konzept 4.7).

Von der Codeaenderung zu den Use Cases: Analyse, Entscheidung, Abdeckung,
Abschluss und Protokoll. Ein geaenderter Anforderungstext ist nie die
bevorzugte Loesung; "Ablehnen" heisst, die Anforderung gilt weiter und der Code
ist zu pruefen.
"""

from __future__ import annotations

import json

from cia.llm.mock import MockProvider
from cia.llm.provider import LlmError
from conftest import api_client

TEXTVORSCHLAG = "Neuer Use-Case-Text"


def _antwort(status="possible_deviation", **felder) -> str:
    antwort = {
        "status": status,
        "affected_passage": "Erfolgsbedingung",
        "reason": "Das Verhalten aendert sich",
        "proposed_text": TEXTVORSCHLAG,
    }
    antwort.update(felder)
    return json.dumps(antwort)


def _code_szenario(client, *aenderungen: dict) -> str:
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    body = {"title": "Code", "direction": "code_to_requirement", "code_changes": list(aenderungen)}
    antwort = client.post(f"/api/baselines/{baseline_id}/scenarios", json=body)
    return antwort.json()["scenario_id"]


def _aenderung(class_id: str, signature: dict | None = None) -> dict:
    eintrag = {"class_id": class_id, "after": "// geaendert"}
    if signature is not None:
        eintrag["signature"] = signature
    return eintrag


def _analysiert(fixture_root, antwort: str | None = None, *aenderungen: dict):
    provider = MockProvider(antwort) if antwort is not None else None
    client = api_client(fixture_root, provider)
    sid = _code_szenario(client, *(aenderungen or (_aenderung("Ausleihe.java"),)))
    lauf = client.post(f"/api/scenarios/{sid}/analyses").json()
    return client, sid, lauf


def _entscheide(client, sid, lauf, kind, use_case_id="UC1", **extra):
    body = {"run_id": lauf["run_id"], "subject_id": use_case_id, "entry_index": 0, "kind": kind}
    body.update(extra)
    return client.post(f"/api/scenarios/{sid}/decisions", json=body)


def _abdeckung(client, sid) -> dict:
    return client.get(f"/api/scenarios/{sid}/coverage").json()["coverage"]


# --- Analyse ------------------------------------------------------------------------------


def test_analyse_fragt_das_modell_je_kandidat_use_case(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())

    assert [r["use_case_id"] for r in lauf["results"]] == ["UC1", "UC2", "UC4"]
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "ready_for_review"


def test_ausgangsfassung_und_aenderung_stehen_im_prompt(fixture_root):
    signatur = {"name": "suche", "parameter_types": ["String"]}
    client, sid, lauf = _analysiert(
        fixture_root, _antwort(), _aenderung("Katalog.java", signatur)
    )

    prompt = lauf["results"][0]["prompt"]

    assert lauf["results"][0]["use_case_id"] == "UC5"
    assert "Katalog.java#suche(String)" in prompt
    assert "titelFragment" in prompt
    assert "// geaendert" in prompt


def test_use_case_wird_gegen_alle_seine_relevanten_aenderungen_geprueft(fixture_root):
    """Konzept 4.4: UC1 gehoert zu Ausleihe.java und Buch.java."""
    client, sid, lauf = _analysiert(
        fixture_root, _antwort(), _aenderung("Ausleihe.java"), _aenderung("Buch.java")
    )

    uc1 = next(r for r in lauf["results"] if r["use_case_id"] == "UC1")

    assert "### Ausleihe.java" in uc1["prompt"]
    assert "### Buch.java" in uc1["prompt"]


def test_standardmock_bewertet_nichts_und_alle_use_cases_bleiben_offen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    abdeckung = _abdeckung(client, sid)

    for ergebnis in lauf["results"]:
        antwort = ergebnis["answer"]
        assert antwort["state"] == "answered"
        assert antwort["assessment"]["status"] == "insufficient_information"
    assert abdeckung["counts"]["insufficient_information"] == 3
    assert {i["kind"] for i in abdeckung["open_items"]} == {"not_assessable"}


def test_klasse_ohne_zuordnung_ist_nicht_zuordenbar_und_bleibt_offen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(), _aenderung("Konfiguration.java"))

    abdeckung = _abdeckung(client, sid)

    assert lauf["results"] == []
    assert lauf["unassignable_class_ids"] == ["Konfiguration.java"]
    assert [(i["kind"], i["ref"]) for i in abdeckung["open_items"]] == [
        ("not_assigned", "Konfiguration.java")
    ]


def test_ausgefallenes_modell_ergibt_keine_antwort(fixture_root):
    class Ausfall:
        name = "ausfall"
        settings: dict = {}

        def complete(self, prompt: str) -> str:
            raise LlmError("Zeitueberschreitung")

    client = api_client(fixture_root, Ausfall())
    sid = _code_szenario(client, _aenderung("Ausleihe.java"))

    lauf = client.post(f"/api/scenarios/{sid}/analyses").json()
    abdeckung = _abdeckung(client, sid)

    for ergebnis in lauf["results"]:
        assert ergebnis["raw_response"] is None
        assert ergebnis["answer"]["state"] == "no_answer"
        assert ergebnis["answer"]["assessment"] is None
    assert abdeckung["counts"]["analyzed_use_cases"] == 0
    assert {i["kind"] for i in abdeckung["open_items"]} == {"not_processed"}


def test_unlesbare_antwort_bleibt_als_rohtext_erhalten(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, "Das weiss ich nicht.")

    ergebnis = lauf["results"][0]

    assert ergebnis["answer"]["state"] == "invalid_format"
    assert ergebnis["raw_response"] == "Das weiss ich nicht."


# --- Entscheidungen -------------------------------------------------------------------------


def test_annahme_heisst_aenderung_gewollt_und_der_vorschlag_bleibt_unveraendert(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())

    antwort = _entscheide(client, sid, lauf, "accepted", revised_proposal="Eigener Text")

    assert antwort.status_code == 201
    assert antwort.json()["revised_proposal"] == "Eigener Text"
    laeufe = client.get(f"/api/scenarios/{sid}/analyses").json()
    assert laeufe[0]["results"][0]["answer"]["assessment"]["proposed_text"] == TEXTVORSCHLAG


def test_ablehnung_heisst_anforderung_gilt_weiter_und_ist_immer_moeglich(fixture_root):
    """Konzept 4.7: Ablehnen kann bedeuten, dass der Code zu pruefen ist."""
    client, sid, lauf = _analysiert(fixture_root, _antwort(proposed_text=None))

    abgelehnt = _entscheide(client, sid, lauf, "rejected")

    assert abgelehnt.status_code == 201


def test_ohne_textvorschlag_laesst_sich_nichts_annehmen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(proposed_text=None))

    antwort = _entscheide(client, sid, lauf, "accepted")

    assert antwort.status_code == 422
    assert "no_proposed_text" in antwort.json()["detail"][0]


def test_unvollstaendige_abweichung_laesst_sich_nicht_annehmen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(reason=""))

    antwort = _entscheide(client, sid, lauf, "accepted")

    assert antwort.status_code == 422
    assert "incomplete" in antwort.json()["detail"][0]


def test_ohne_erkennbare_abweichung_gibt_es_nichts_zu_entscheiden(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(status="no_deviation_visible"))

    assert _entscheide(client, sid, lauf, "accepted").status_code == 422
    assert _entscheide(client, sid, lauf, "rejected").status_code == 422


def test_entscheidung_zu_use_case_ohne_eintrag_wird_abgewiesen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())

    assert _entscheide(client, sid, lauf, "rejected", use_case_id="UC5").status_code == 422
    falsche_nummer = client.post(
        f"/api/scenarios/{sid}/decisions",
        json={"run_id": lauf["run_id"], "subject_id": "UC1", "entry_index": 1, "kind": "rejected"},
    )
    assert falsche_nummer.status_code == 422


# --- Abdeckung und Abschluss -----------------------------------------------------------------


def test_abdeckung_zaehlt_use_cases_und_entscheidungen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())
    _entscheide(client, sid, lauf, "accepted", use_case_id="UC1")
    _entscheide(client, sid, lauf, "rejected", use_case_id="UC2")

    zaehlwerte = _abdeckung(client, sid)["counts"]

    assert zaehlwerte["imported_use_cases"] == 6
    assert zaehlwerte["candidate_use_cases"] == 3
    assert zaehlwerte["analyzed_use_cases"] == 3
    assert zaehlwerte["proposals"] == 3
    assert zaehlwerte["proposals_accepted"] == 1
    assert zaehlwerte["proposals_rejected"] == 1
    assert zaehlwerte["proposals_undecided"] == 1


def test_undecidierte_abweichung_ist_ein_offener_fall(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())

    offen = _abdeckung(client, sid)["open_items"]

    assert {i["kind"] for i in offen} == {"proposal_undecided"}
    assert [i["ref"] for i in offen] == ["UC1", "UC2", "UC4"]


def test_kein_bedarf_erkennbar_wird_gezaehlt_und_haelt_den_abschluss_nicht_auf(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(status="no_deviation_visible"))

    zaehlwerte = _abdeckung(client, sid)["counts"]
    abschluss = client.post(f"/api/scenarios/{sid}/close", json={})

    assert zaehlwerte["no_deviation_visible"] == 3
    assert _abdeckung(client, sid)["open_items"] == []
    assert abschluss.status_code == 200


def test_abschluss_mit_offener_abweichung_braucht_bestaetigung(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())

    ohne = client.post(f"/api/scenarios/{sid}/close", json={})
    mit = client.post(
        f"/api/scenarios/{sid}/close",
        json={"acknowledge_open_items": True, "note": "Wird spaeter geklaert"},
    )

    assert ohne.status_code == 409
    assert mit.status_code == 200
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "closed"


# --- Protokoll ------------------------------------------------------------------------------


def test_protokoll_haelt_eingabe_ausgabe_und_entscheidung_je_use_case_fest(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort())
    _entscheide(client, sid, lauf, "accepted", revised_proposal="Eigener Text")

    eintraege = client.get(f"/api/scenarios/{sid}/protocol").json()

    anfrage = next(e for e in eintraege if e["kind"] == "model_request")
    antwort = next(e for e in eintraege if e["kind"] == "model_response")
    entscheidung = next(e for e in eintraege if e["kind"] == "decision")
    assert anfrage["data"]["use_case_id"] == "UC1"
    assert "USE CASE: UC1" in anfrage["data"]["prompt"]
    assert "raw_response" not in anfrage["data"]
    assert antwort["data"]["raw_response"] == _antwort()
    assert entscheidung["data"]["target"] == "UC1"
    assert entscheidung["data"]["original_proposal"] == TEXTVORSCHLAG
    assert entscheidung["data"]["decision"]["revised_proposal"] == "Eigener Text"


def test_nicht_zuordenbare_klasse_steht_am_ende_des_laufs_im_protokoll(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, _antwort(), _aenderung("Konfiguration.java"))

    eintraege = client.get(f"/api/scenarios/{sid}/protocol").json()

    ende = next(e for e in eintraege if e["kind"] == "analysis_finished")
    assert ende["data"]["unassignable_class_ids"] == ["Konfiguration.java"]
