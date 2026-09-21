"""Protokoll fuer die spaetere Auswertung (F7, Konzept 4.13).

Das Protokoll muss Eingabe, Ausgabe und Entscheidung getrennt festhalten,
Zeitpunkte tragen und offene Faelle (Ausfall, Abbruch, nicht verarbeitete
Klasse) als solche zeigen.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from cia.api.protocol import Protocol
from cia.domain.ids import BaselineId, ClassId, ScenarioId
from cia.llm.mock import MockProvider
from cia.llm.provider import LlmError
from cia.llm.run import AnalysisRun, ClassResult
from conftest import api_client, neues_szenario
from test_decisions import ANTWORT_MIT_VORSCHLAG, VORSCHLAG


def _protokoll(client, sid: str) -> list[dict]:
    return client.get(f"/api/scenarios/{sid}/protocol").json()


def _arten(eintraege: list[dict]) -> list[str]:
    return [e["kind"] for e in eintraege]


def _analysiert(fixture_root, provider=None, **kwargs):
    client = api_client(fixture_root, provider or MockProvider(ANTWORT_MIT_VORSCHLAG), **kwargs)
    sid = neues_szenario(client, "UC5")
    lauf = client.post(f"/api/scenarios/{sid}/analyses").json()
    return client, sid, lauf


def test_protokoll_haelt_ausgangsstand_und_auftrag_fest(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    erster = _protokoll(client, sid)[0]

    assert erster["kind"] == "scenario_created"
    assert erster["data"]["baseline"]["counts"]["trace_links"] == 14
    aenderung = erster["data"]["scenario"]["requirement_changes"][0]
    assert (aenderung["kind"], aenderung["use_case_id"]) == ("deactivate", "UC5")


def test_zustandswechsel_stehen_mit_zeitpunkt_im_protokoll(fixture_root):
    client, sid, _ = _analysiert(fixture_root)

    wechsel = [e for e in _protokoll(client, sid) if e["kind"] == "state_changed"]

    assert [(w["data"]["from"], w["data"]["to"]) for w in wechsel] == [
        ("created", "structurally_checked"),
        ("structurally_checked", "analysis_running"),
        ("analysis_running", "ready_for_review"),
    ]
    assert all(w["time"] for w in wechsel)


def test_eingabe_und_ausgabe_stehen_in_getrennten_eintraegen(fixture_root):
    client, sid, _ = _analysiert(fixture_root)

    eintraege = _protokoll(client, sid)
    anfragen = [e for e in eintraege if e["kind"] == "model_request"]
    antworten = [e for e in eintraege if e["kind"] == "model_response"]

    assert len(anfragen) == len(antworten) == 2
    for anfrage in anfragen:
        assert f"KLASSE: {anfrage['data']['class_id']}" in anfrage["data"]["prompt"]
        assert "raw_response" not in anfrage["data"]
        assert anfrage["data"]["prompt_version"]
        assert anfrage["data"]["provider"] == "mock"
    for antwort in antworten:
        assert "prompt" not in antwort["data"]
        assert antwort["data"]["raw_response"] == ANTWORT_MIT_VORSCHLAG


def test_anfrage_steht_vor_ihrer_antwort_und_zeitpunkte_sind_geordnet(fixture_root):
    client, sid, _ = _analysiert(fixture_root)

    eintraege = _protokoll(client, sid)
    for klasse in ("Buch.java", "Katalog.java"):
        anfrage = next(
            e for e in eintraege if e["kind"] == "model_request" and e["data"]["class_id"] == klasse
        )
        antwort = next(
            e for e in eintraege if e["kind"] == "model_response" and e["data"]["class_id"] == klasse
        )
        assert anfrage["seq"] < antwort["seq"]
        gestellt = datetime.fromisoformat(anfrage["data"]["requested_at"])
        zurueck = datetime.fromisoformat(antwort["data"]["finished_at"])
        assert gestellt <= zurueck


def test_eintraege_sind_fortlaufend_nummeriert(fixture_root):
    client, sid, _ = _analysiert(fixture_root)

    nummern = [e["seq"] for e in _protokoll(client, sid)]

    assert nummern == list(range(1, len(nummern) + 1))


def test_entscheidung_traegt_ursprungsvorschlag_und_ueberarbeitung_getrennt(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)
    client.post(
        f"/api/scenarios/{sid}/decisions",
        json={
            "run_id": lauf["run_id"],
            "subject_id": "Katalog.java",
            "entry_index": 0,
            "kind": "accepted",
            "revised_proposal": "Methode nur deaktivieren",
        },
    )

    entscheidung = next(e for e in _protokoll(client, sid) if e["kind"] == "decision")

    assert entscheidung["data"]["target"] == "suche(String)"
    assert entscheidung["data"]["original_proposal"] == VORSCHLAG
    assert entscheidung["data"]["decision"]["revised_proposal"] == "Methode nur deaktivieren"
    assert entscheidung["data"]["decision"]["kind"] == "accepted"


def test_ausgefallenes_modell_steht_als_fehlende_antwort_im_protokoll(fixture_root):
    class Ausfall:
        name = "ausfall"
        settings: dict = {}

        def complete(self, prompt: str) -> str:
            raise LlmError("Zeitueberschreitung")

    client, sid, _ = _analysiert(fixture_root, Ausfall())

    antworten = [e for e in _protokoll(client, sid) if e["kind"] == "model_response"]

    assert antworten
    for antwort in antworten:
        assert antwort["data"]["raw_response"] is None
        assert antwort["data"]["answer"]["state"] == "no_answer"


def test_abbruch_durch_unerwarteten_fehler_steht_im_protokoll(fixture_root):
    class Kaputt:
        name = "kaputt"
        settings: dict = {}

        def complete(self, prompt: str) -> str:
            raise RuntimeError("unerwartet")

    client = api_client(fixture_root, Kaputt(), raise_server_exceptions=False)
    sid = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{sid}/analyses")

    eintraege = _protokoll(client, sid)

    assert "analysis_aborted" in _arten(eintraege)
    letzter_wechsel = [e for e in eintraege if e["kind"] == "state_changed"][-1]
    assert letzter_wechsel["data"]["to"] == "structurally_checked"


def test_verwerfen_steht_im_protokoll(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{sid}/discard")

    letzter = _protokoll(client, sid)[-1]

    assert letzter["kind"] == "state_changed"
    assert letzter["data"]["to"] == "discarded"


def test_aenderung_ohne_zuordnung_steht_am_ende_des_laufs(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC6")
    client.post(f"/api/scenarios/{sid}/analyses")

    ende = next(e for e in _protokoll(client, sid) if e["kind"] == "analysis_finished")

    assert [u["use_case_id"] for u in ende["data"]["unresolved"]] == ["UC6"]


def test_nicht_verarbeitete_klasse_wird_als_solche_protokolliert():
    """Konzept 4.13: Nicht verarbeitete Artefakte muessen erkennbar sein."""
    jetzt = datetime.now(timezone.utc)
    lauf = AnalysisRun(
        run_id="r1",
        scenario_id=ScenarioId("s1"),
        baseline_id=BaselineId("b"),
        started_at=jetzt,
        finished_at=jetzt,
        provider_name="mock",
        provider_settings={},
        prompt_version="v",
        results=(ClassResult(ClassId("K.java"), "Klasse wurde nicht verarbeitet", None),),
        unresolved=(),
    )
    protokoll = Protocol()

    protokoll.record_run(lauf)

    arten = [e["kind"] for e in protokoll.records("s1")]
    assert arten == ["class_not_processed", "analysis_finished"]
    assert protokoll.records("s1")[0]["data"]["reason"] == "Klasse wurde nicht verarbeitet"


def test_protokoll_wird_zeilenweise_in_eine_datei_geschrieben(fixture_root, tmp_path):
    client, sid, _ = _analysiert(fixture_root, protocol_dir=tmp_path)

    im_speicher = _protokoll(client, sid)
    zeilen = (tmp_path / f"{sid}.jsonl").read_text(encoding="utf-8").splitlines()

    assert len(zeilen) == len(im_speicher)
    assert [json.loads(z) for z in zeilen] == im_speicher


def test_protokolle_verschiedener_szenarien_bleiben_getrennt(fixture_root, tmp_path):
    client = api_client(fixture_root, protocol_dir=tmp_path)
    erstes = neues_szenario(client, "UC5")
    zweites = neues_szenario(client, "UC1")

    assert {e["scenario_id"] for e in _protokoll(client, erstes)} == {erstes}
    assert {e["scenario_id"] for e in _protokoll(client, zweites)} == {zweites}
    assert (tmp_path / f"{erstes}.jsonl").exists()
    assert (tmp_path / f"{zweites}.jsonl").exists()


def test_unbekanntes_szenario_liefert_404(fixture_root):
    client = api_client(fixture_root)

    assert client.get("/api/scenarios/gibt-es-nicht/protocol").status_code == 404
