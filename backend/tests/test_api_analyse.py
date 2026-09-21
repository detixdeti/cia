"""Analyse durch das Modell ueber die Schnittstelle (F4).

Alle Tests arbeiten mit dem Mock oder einem absichtlich fehlerhaften Anbieter.
Im Mittelpunkt steht, dass offene Faelle offen bleiben: Ein Ausfall, eine
unlesbare Antwort oder eine unbeantwortete Methode wird nie zur Entwarnung
(Konzept 4.5 und 4.12).
"""

from __future__ import annotations

import json

from cia.llm.mock import MockProvider
from cia.llm.provider import LlmError
from conftest import api_client, neues_szenario


def _starte(client, scenario_id: str):
    return client.post(f"/api/scenarios/{scenario_id}/analyses")


def _ergebnisse(lauf: dict) -> dict:
    return {r["class_id"]: r for r in lauf["results"]}


class _AusfallenderAnbieter:
    name = "ausfall"
    settings: dict = {}

    def complete(self, prompt: str) -> str:
        raise LlmError("Zeitueberschreitung")


class _KaputterAnbieter:
    name = "kaputt"
    settings: dict = {}

    def complete(self, prompt: str) -> str:
        raise RuntimeError("unerwarteter Fehler")


def test_analyse_liefert_ein_ergebnis_je_kandidatenklasse(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    antwort = _starte(client, sid)

    assert antwort.status_code == 201
    assert set(_ergebnisse(antwort.json())) == {"Buch.java", "Katalog.java"}


def test_standardmock_bewertet_nichts_und_alle_methoden_bleiben_offen(fixture_root):
    """Der Mock im laufenden Prototyp taeuscht keine Beurteilung vor."""
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    sid = neues_szenario(client, "UC5")

    lauf = _starte(client, sid).json()

    katalog = _ergebnisse(lauf)["Katalog.java"]["analysis"]["answer"]
    methoden = client.get(f"/api/baselines/{baseline_id}/classes/Katalog.java").json()["methods"]
    assert katalog["state"] == "answered"
    assert katalog["entries"] == []
    assert len(katalog["unanswered_methods"]) == len(methoden)


def test_szenario_ist_nach_der_analyse_bereit_zur_pruefung(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    _starte(client, sid)

    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "ready_for_review"


def test_prompt_und_rohantwort_stehen_im_ergebnis(fixture_root):
    """Konzept 4.13: Prompt, Vorlagenversion und erhaltene Antwort werden festgehalten."""
    antwort_text = json.dumps({"entries": []})
    client = api_client(fixture_root, MockProvider(antwort_text))
    sid = neues_szenario(client, "UC5")

    lauf = _starte(client, sid).json()

    katalog = _ergebnisse(lauf)["Katalog.java"]["analysis"]
    assert "suche(String, String)" in katalog["prompt"]
    assert katalog["raw_response"] == antwort_text
    assert katalog["prompt_version"] == lauf["prompt_version"]
    assert lauf["provider_name"] == "mock"


def test_antwort_wird_der_richtigen_methode_zugeordnet_und_unbekanntes_bleibt_sichtbar(
    fixture_root,
):
    """Der Mock antwortet fuer jede Klasse gleich. Fuer Katalog.java gibt es die
    Methode, fuer Buch.java nicht. Dort bleibt der Eintrag als Problem stehen."""
    antwort_text = json.dumps(
        {
            "entries": [
                {
                    "target_kind": "method",
                    "target": "suche(String)",
                    "status": "change_proposed",
                    "use_case_passage": "Das System liefert die passenden Titel",
                    "reason": "UC5 entfaellt",
                    "proposal": "Methode entfernen",
                }
            ]
        }
    )
    client = api_client(fixture_root, MockProvider(antwort_text))
    sid = neues_szenario(client, "UC5")

    ergebnisse = _ergebnisse(_starte(client, sid).json())

    katalog = ergebnisse["Katalog.java"]["analysis"]["answer"]["entries"][0]
    assert katalog["method_ref"]["class_id"] == "Katalog.java"
    assert katalog["problems"] == []
    buch = ergebnisse["Buch.java"]["analysis"]["answer"]["entries"][0]
    assert buch["method_ref"] is None
    assert buch["problems"] == ["unknown_method"]


def test_ausgefallenes_modell_ergibt_keine_antwort_und_keine_entwarnung(fixture_root):
    client = api_client(fixture_root, _AusfallenderAnbieter())
    sid = neues_szenario(client, "UC5")

    lauf = _starte(client, sid).json()

    for ergebnis in lauf["results"]:
        antwort = ergebnis["analysis"]["answer"]
        assert antwort["state"] == "no_answer"
        assert ergebnis["analysis"]["raw_response"] is None
        assert antwort["unanswered_methods"]
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "ready_for_review"


def test_unlesbare_antwort_bleibt_als_rohtext_erhalten(fixture_root):
    client = api_client(fixture_root, MockProvider("Das weiss ich nicht."))
    sid = neues_szenario(client, "UC5")

    lauf = _starte(client, sid).json()

    analyse = _ergebnisse(lauf)["Katalog.java"]["analysis"]
    assert analyse["answer"]["state"] == "invalid_format"
    assert analyse["raw_response"] == "Das weiss ich nicht."


def test_aenderung_ohne_zuordnung_steht_im_lauf_als_offen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC6")

    lauf = _starte(client, sid).json()

    assert lauf["results"] == []
    assert [u["use_case_id"] for u in lauf["unresolved"]] == ["UC6"]


def test_zweite_analyse_erzeugt_einen_neuen_lauf_und_der_erste_bleibt(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    erster = _starte(client, sid).json()
    zweiter = _starte(client, sid).json()

    laeufe = client.get(f"/api/scenarios/{sid}/analyses").json()
    assert [l["run_id"] for l in laeufe] == [erster["run_id"], zweiter["run_id"]]
    assert erster["run_id"] != zweiter["run_id"]
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "ready_for_review"


def test_verworfenes_szenario_wird_nicht_analysiert(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{sid}/discard")

    assert _starte(client, sid).status_code == 409


def test_unerwarteter_fehler_laesst_das_szenario_nicht_in_analyse_laeuft_haengen(fixture_root):
    client = api_client(fixture_root, _KaputterAnbieter(), raise_server_exceptions=False)
    sid = neues_szenario(client, "UC5")

    antwort = _starte(client, sid)

    assert antwort.status_code == 500
    assert client.get(f"/api/scenarios/{sid}").json()["state"] == "structurally_checked"
    assert client.get(f"/api/scenarios/{sid}/analyses").json() == []


def test_unbekanntes_szenario_liefert_404(fixture_root):
    client = api_client(fixture_root)

    assert _starte(client, "gibt-es-nicht").status_code == 404
    assert client.get("/api/scenarios/gibt-es-nicht/analyses").status_code == 404
